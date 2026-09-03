/**
 * Terminal Monitor: Observes command execution and process exit codes.
 */

import * as vscode from 'vscode';
import * as cp from 'child_process';
import { v4 as uuidv4 } from 'uuid';
import { WebSocketClient } from '../transport/websocket-client';
import { SessionManager } from '../utils/session-manager';
import { Sanitizer } from '../utils/sanitizer';
import { TerminalCommandPayload, TesseractEvent } from '../types/events';

export class TerminalMonitor {
    private client: WebSocketClient;
    private sessionMgr: SessionManager;
    private enabled: boolean;

    constructor(client: WebSocketClient, enabled: boolean = true) {
        this.client = client;
        this.sessionMgr = SessionManager.getInstance();
        this.enabled = enabled;
    }

    public register(context: vscode.ExtensionContext): void {
        if (!this.enabled) return;

        // Terminal execution / exit code observation
        if ('onDidEndTerminalShellExecution' in (vscode.window as Record<string, unknown>)) {
            // Newer VS Code Shell Integration API (1.90+)
            const win = vscode.window as unknown as {
                onDidEndTerminalShellExecution: (
                    listener: (e: {
                        execution: { commandLine: { value: string } };
                        exitCode?: number;
                    }) => void
                ) => vscode.Disposable;
            };
            context.subscriptions.push(
                win.onDidEndTerminalShellExecution((e) => {
                    const rawCommand = e.execution.commandLine.value || '';
                    const cleanCommand = Sanitizer.sanitizeText(rawCommand);
                    const lowerCmd = cleanCommand.toLowerCase();

                    // Detect active file & language
                    const activeDoc = vscode.window.activeTextEditor?.document;
                    let detectedFilePath = activeDoc ? Sanitizer.formatFilePath(activeDoc.uri) : undefined;
                    let detectedLang = activeDoc ? activeDoc.languageId : undefined;

                    if (lowerCmd.includes('python') || lowerCmd.includes('.py')) {
                        detectedLang = 'python';
                    } else if (lowerCmd.includes('node') || lowerCmd.includes('.js') || lowerCmd.includes('.ts')) {
                        detectedLang = 'javascript';
                    } else if (lowerCmd.includes('gcc') || lowerCmd.includes('clang') || lowerCmd.includes('.c')) {
                        detectedLang = 'c';
                    }

                    const payload: TerminalCommandPayload & { file_path?: string; language?: string; topic?: string } = {
                        command: cleanCommand,
                        exit_code: e.exitCode,
                        file_path: detectedFilePath,
                        language: detectedLang,
                        topic: detectedLang
                    };
                    this.emitEvent('terminal_command', payload);

                    // If terminal command failed, capture the exact runtime error & code snippet
                    if (e.exitCode !== undefined && e.exitCode !== 0 && detectedFilePath) {
                        const execCmd = detectedLang === 'python' ? `python "${detectedFilePath}"` :
                                        detectedLang === 'javascript' ? `node "${detectedFilePath}"` : cleanCommand;

                        cp.exec(execCmd, { timeout: 2500 }, (err, stdout, stderr) => {
                            const combined = (stderr || stdout || err?.message || '').trim();
                            if (!combined) return;

                            let errorLine: number | undefined;
                            let errorMsg = combined;

                            const pyLineMatch = combined.match(/line (\d+)/i);
                            const jsLineMatch = combined.match(/:(\d+):\d+/);
                            if (pyLineMatch) {
                                errorLine = parseInt(pyLineMatch[1], 10);
                            } else if (jsLineMatch) {
                                errorLine = parseInt(jsLineMatch[1], 10);
                            }

                            const lines = combined.split('\n').map(l => l.trim()).filter(Boolean);
                            if (lines.length > 0) {
                                errorMsg = lines[lines.length - 1];
                            }

                            let snippet = '';
                            if (activeDoc) {
                                const docLines = activeDoc.getText().split('\n');
                                if (errorLine && errorLine > 0 && errorLine <= docLines.length) {
                                    const start = Math.max(0, errorLine - 4);
                                    const end = Math.min(docLines.length, errorLine + 3);
                                    snippet = docLines.slice(start, end).join('\n');
                                } else {
                                    snippet = docLines.slice(0, 25).join('\n');
                                }
                            }

                            this.emitEvent('error_detected', {
                                file_path: detectedFilePath,
                                language: detectedLang,
                                topic: detectedLang,
                                error_message: errorMsg,
                                error_line: errorLine,
                                code_snippet: snippet,
                                full_traceback: combined.slice(0, 800),
                                severity: 'error',
                                source: 'terminal_execution'
                            });
                        });
                    }
                })
            );
        } else {
            // Fallback: Terminal close event
            context.subscriptions.push(
                vscode.window.onDidCloseTerminal((terminal) => {
                    if (terminal.exitStatus) {
                        const activeDoc = vscode.window.activeTextEditor?.document;
                        const detectedLang = activeDoc ? activeDoc.languageId : undefined;
                        const payload: TerminalCommandPayload & { language?: string; topic?: string } = {
                            command: `[Terminal: ${terminal.name}]`,
                            exit_code: terminal.exitStatus.code,
                            language: detectedLang,
                            topic: detectedLang
                        };
                        this.emitEvent('terminal_command', payload);
                    }
                })
            );
        }
    }

    private emitEvent<T extends Record<string, unknown>>(
        eventType: import('../types/events').EventType,
        payload: T
    ): void {
        const event: TesseractEvent<T> = {
            event_id: uuidv4(),
            source: 'vscode',
            event_type: eventType,
            timestamp: new Date().toISOString(),
            payload,
            metadata: {
                session_id: this.sessionMgr.getSessionId(),
                sequence_number: this.sessionMgr.nextSequence(),
                confidence: 1.0,
                privacy_level: 'local_only',
                version: '0.1.0',
            },
        };
        this.client.send(event as unknown as TesseractEvent);
    }
}
