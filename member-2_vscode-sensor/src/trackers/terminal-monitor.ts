/**
 * Terminal Monitor: Observes command execution and process exit codes.
 */

import * as vscode from 'vscode';
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

                    const payload: TerminalCommandPayload = {
                        command: cleanCommand,
                        exit_code: e.exitCode,
                    };
                    this.emitEvent('terminal_command', payload);
                })
            );
        } else {
            // Fallback: Terminal close event
            context.subscriptions.push(
                vscode.window.onDidCloseTerminal((terminal) => {
                    if (terminal.exitStatus) {
                        const payload: TerminalCommandPayload = {
                            command: `[Terminal: ${terminal.name}]`,
                            exit_code: terminal.exitStatus.code,
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
