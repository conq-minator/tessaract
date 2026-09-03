/**
 * Tesseract VS Code Sensor Extension Entry Point.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { WebSocketClient, ConnectionStatus } from './transport/websocket-client';
import { Logger } from './utils/logger';
import { EditorTracker } from './trackers/editor-tracker';
import { DiagnosticWatcher } from './trackers/diagnostic-watcher';
import { TerminalMonitor } from './trackers/terminal-monitor';
import { DebugTracker } from './trackers/debug-tracker';
import { SessionManager } from './utils/session-manager';

let client: WebSocketClient | null = null;
let statusBarItem: vscode.StatusBarItem | null = null;

export function activate(context: vscode.ExtensionContext): void {
    Logger.initialize(context);
    Logger.info('Activating Tesseract VS Code Sensor...');

    const config = vscode.workspace.getConfiguration('tesseract');
    const wsUrl = config.get<string>('coreWsUrl') || 'ws://localhost:9700/events';
    
    // Read shared secret from VS Code config or workspace .env fallback
    let sharedSecret = config.get<string>('sharedSecret') || '';
    if (!sharedSecret) {
        sharedSecret = findSharedSecretInWorkspace();
    }

    const bufferSize = config.get<number>('bufferSize') || 100;
    const reconnectIntervalMs = config.get<number>('reconnectIntervalMs') || 5000;
    const editDebounceMs = config.get<number>('editDebounceMs') || 2000;
    const terminalCapture = config.get<boolean>('terminalCapture') ?? true;

    // Initialize WebSocket Client
    client = new WebSocketClient(wsUrl, sharedSecret, bufferSize, reconnectIntervalMs);

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
    Logger.info('Tesseract VS Code Sensor deactivated.');
}
