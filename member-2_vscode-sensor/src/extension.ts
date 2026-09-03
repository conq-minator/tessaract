/**
 * Tesseract VS Code Sensor Extension Entry Point.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { exec } from 'child_process';
import { v4 as uuidv4 } from 'uuid';
import { WebSocketClient, ConnectionStatus } from './transport/websocket-client';
import { AlertListener } from './transport/alert-listener';
import { Logger } from './utils/logger';
import { EditorTracker } from './trackers/editor-tracker';
import { DiagnosticWatcher } from './trackers/diagnostic-watcher';
import { TerminalMonitor } from './trackers/terminal-monitor';
import { DebugTracker } from './trackers/debug-tracker';
import { SessionManager } from './utils/session-manager';

let client: WebSocketClient | null = null;
let alertListener: AlertListener | null = null;
let statusBarItem: vscode.StatusBarItem | null = null;

export function activate(context: vscode.ExtensionContext): void {
    Logger.initialize(context);
    Logger.info('Activating Tesseract VS Code Sensor...');

    const config = vscode.workspace.getConfiguration('tesseract');
    let wsUrl = config.get<string>('coreWsUrl') || 'ws://127.0.0.1:9700/events';
    if (wsUrl.includes('localhost')) {
        wsUrl = wsUrl.replace('localhost', '127.0.0.1');
    }
    
    // Read shared secret from VS Code config or workspace .env fallback
    let sharedSecret = config.get<string>('sharedSecret') || '';
    if (!sharedSecret) {
        sharedSecret = findSharedSecretInWorkspace() || 'rQUSMHvr5MVgVdCH-b8seB7UbRYeykyJYjBzaZeN2Pk';
    }

    const bufferSize = config.get<number>('bufferSize') || 100;
    const reconnectIntervalMs = config.get<number>('reconnectIntervalMs') || 5000;
    const editDebounceMs = config.get<number>('editDebounceMs') || 2000;
    const terminalCapture = config.get<boolean>('terminalCapture') ?? true;

    // Initialize Outbound Event Stream
    client = new WebSocketClient(wsUrl, sharedSecret, bufferSize, reconnectIntervalMs);

    // Initialize Inbound Alert Stream for in-editor notifications
    const alertsUrl = wsUrl.replace(/\/events\b/, '/alerts');
    alertListener = new AlertListener(alertsUrl, sharedSecret);
    alertListener.connect();

    // Setup Status Bar
    setupStatusBar(context);

    // Listen to Connection Status updates
    client.onStatusChange((status) => {
        updateStatusBar(status);
    });

    // Register User Commands
    context.subscriptions.push(
        vscode.commands.registerCommand('tesseract.toggleSensor', () => {
            if (!client) return;
            if (client.isRunning()) {
                client.pause();
                vscode.window.showInformationMessage('Tesseract Sensor: Paused');
            } else {
                client.resume();
                vscode.window.showInformationMessage('Tesseract Sensor: Resumed & Connected');
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('tesseract.showHealth', () => {
            const sessionMgr = SessionManager.getInstance();
            const status = client?.isRunning() ? 'Active' : 'Paused';
            vscode.window.showInformationMessage(
                `Tesseract Sensor: ${status} | Session: ${sessionMgr.getSessionId().slice(0, 8)}...`
            );
            Logger.show();
        })
    );

    // Register Tesseract: Run Active File
    context.subscriptions.push(
        vscode.commands.registerCommand('tesseract.runFile', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showInformationMessage('Open a code file to run with Tesseract.');
                return;
            }
            const doc = editor.document;
            await doc.save();
            const filePath = doc.fileName;
            const lang = doc.languageId;
            const sessionMgr = SessionManager.getInstance();

            // Emit file_saved event
            client?.send({
                event_id: uuidv4(),
                source: 'vscode',
                event_type: 'file_saved',
                timestamp: new Date().toISOString(),
                payload: {
                    file_path: filePath,
                    language: lang,
                    change_size: doc.getText().length,
                    line_count: doc.lineCount
                },
                metadata: {
                    session_id: sessionMgr.getSessionId(),
                    sequence_number: sessionMgr.nextSequence(),
                    confidence: 1.0,
                    privacy_level: 'local_only',
                    version: '0.1.0'
                }
            });

            // Determine command line
            let cmd = '';
            if (lang === 'python') {
                cmd = `python "${filePath}"`;
            } else if (lang === 'c' || lang === 'cpp') {
                cmd = `gcc "${filePath}" -o "${filePath}.exe" && "${filePath}.exe"`;
            } else if (lang === 'javascript') {
                cmd = `node "${filePath}"`;
            } else {
                cmd = `python "${filePath}"`;
            }

            // Run in terminal
            const term = vscode.window.terminals.find(t => t.name === 'Tesseract Terminal') || vscode.window.createTerminal('Tesseract Terminal');
            term.show(true);
            term.sendText(cmd);

            // Execute in background to capture exit code & runtime errors
            exec(cmd, { cwd: path.dirname(filePath) }, (err, stdout, stderr) => {
                const exitCode = err ? (err.code || 1) : 0;
                
                // Emit terminal command event
                client?.send({
                    event_id: uuidv4(),
                    source: 'vscode',
                    event_type: 'terminal_command',
                    timestamp: new Date().toISOString(),
                    payload: {
                        command: cmd,
                        exit_code: exitCode
                    },
                    metadata: {
                        session_id: sessionMgr.getSessionId(),
                        sequence_number: sessionMgr.nextSequence(),
                        confidence: 1.0,
                        privacy_level: 'local_only',
                        version: '0.1.0'
                    }
                });

                if (err) {
                    const cleanErr = (stderr || stdout || err.message).trim().slice(0, 300);
                    // Emit error_detected event
                    client?.send({
                        event_id: uuidv4(),
                        source: 'vscode',
                        event_type: 'error_detected',
                        timestamp: new Date().toISOString(),
                        payload: {
                            file_path: filePath,
                            language: (lang === 'python' || filePath.endsWith('.py')) ? 'python' : lang,
                            topic: (lang === 'python' || filePath.endsWith('.py')) ? 'python' : undefined,
                            error_message: cleanErr,
                            error_line: 1,
                            severity: 'error',
                            source: 'runtime'
                        },
                        metadata: {
                            session_id: sessionMgr.getSessionId(),
                            sequence_number: sessionMgr.nextSequence(),
                            confidence: 1.0,
                            privacy_level: 'local_only',
                            version: '0.1.0'
                        }
                    });
                }
            });
        })
    );

    // Register Trackers
    const editorTracker = new EditorTracker(client, editDebounceMs);
    editorTracker.register(context);

    const diagWatcher = new DiagnosticWatcher(client);
    diagWatcher.register(context);

    const termMonitor = new TerminalMonitor(client, terminalCapture);
    termMonitor.register(context);

    const debugTracker = new DebugTracker(client);
    debugTracker.register(context);

    // Watch for configuration changes
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration((e) => {
            if (e.affectsConfiguration('tesseract') && client) {
                const newConfig = vscode.workspace.getConfiguration('tesseract');
                const newUrl = newConfig.get<string>('coreWsUrl') || 'ws://localhost:9700/events';
                let newSecret = newConfig.get<string>('sharedSecret') || '';
                if (!newSecret) newSecret = findSharedSecretInWorkspace();
                client.updateConfig(newUrl, newSecret);
            }
        })
    );

    // Start WebSocket Connection
    client.connect();
    Logger.info('Tesseract VS Code Sensor successfully activated.');
}

function setupStatusBar(context: vscode.ExtensionContext): void {
    statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );
    statusBarItem.command = 'tesseract.toggleSensor';
    statusBarItem.tooltip = 'Click to toggle Tesseract Sensor tracking';
    updateStatusBar('connecting');
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);
}

function updateStatusBar(status: ConnectionStatus): void {
    if (!statusBarItem) return;

    switch (status) {
        case 'connected':
            statusBarItem.text = '$(broadcast) Tesseract: Active';
            statusBarItem.backgroundColor = undefined;
            statusBarItem.tooltip = 'Tesseract Sensor: Connected & Streaming (Click to Pause)';
            break;
        case 'connecting':
            statusBarItem.text = '$(sync~spin) Tesseract: Connecting';
            statusBarItem.backgroundColor = undefined;
            statusBarItem.tooltip = 'Connecting to Tesseract Core Engine...';
            break;
        case 'disconnected':
            statusBarItem.text = '$(circle-slash) Tesseract: Offline';
            statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            statusBarItem.tooltip = 'Core Engine unreachable. Events will buffer locally.';
            break;
        case 'paused':
            statusBarItem.text = '$(debug-pause) Tesseract: Paused';
            statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
            statusBarItem.tooltip = 'Tesseract Sensor is paused. Click to Resume.';
            break;
    }
}

function findSharedSecretInWorkspace(): string {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders) return '';

    for (const folder of folders) {
        const envCandidates = [
            path.join(folder.uri.fsPath, '.env'),
            path.join(folder.uri.fsPath, 'member-4_core-engine', '.env'),
            path.join(folder.uri.fsPath, 'member-6_tutor-ui', '.env'),
        ];

        for (const envFile of envCandidates) {
            if (fs.existsSync(envFile)) {
                try {
                    const content = fs.readFileSync(envFile, 'utf8');
                    const match = content.match(/TESSERACT_SHARED_SECRET\s*=\s*([^\r\n]+)/);
                    if (match && match[1]) {
                        return match[1].trim();
                    }
                } catch (e) {
                    // ignore
                }
            }
        }
    }
    return '';
}

export function deactivate(): void {
    if (client) {
        client.disconnect();
        client = null;
    }
    if (alertListener) {
        alertListener.disconnect();
        alertListener = null;
    }
    Logger.info('Tesseract VS Code Sensor deactivated.');
}
