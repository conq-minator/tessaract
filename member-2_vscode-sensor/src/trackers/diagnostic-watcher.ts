/**
 * Diagnostic & Error Watcher: Observes compiler and linter errors across files.
 */

import * as vscode from 'vscode';
import { v4 as uuidv4 } from 'uuid';
import { WebSocketClient } from '../transport/websocket-client';
import { SessionManager } from '../utils/session-manager';
import { Sanitizer } from '../utils/sanitizer';
import { ErrorDetectedPayload, ErrorResolvedPayload, TesseractEvent } from '../types/events';

export class DiagnosticWatcher {
    private client: WebSocketClient;
    private sessionMgr: SessionManager;
    // Map of "filePath:line:message" to track active diagnostics and detect resolution
    private activeDiagnostics: Set<string> = new Set();

    constructor(client: WebSocketClient) {
        this.client = client;
        this.sessionMgr = SessionManager.getInstance();
    }

    public register(context: vscode.ExtensionContext): void {
        context.subscriptions.push(
            vscode.languages.onDidChangeDiagnostics((e) => {
                for (const uri of e.uris) {
                    if (uri.scheme !== 'file') continue;
                    this.processDiagnosticsForUri(uri);
                }
            })
        );
    }

    private processDiagnosticsForUri(uri: vscode.Uri): void {
        const diagnostics = vscode.languages.getDiagnostics(uri);
        const filePath = Sanitizer.formatFilePath(uri);
        const currentUriDiags = new Set<string>();

        for (const diag of diagnostics) {
            // Only care about Errors and Warnings
            if (
                diag.severity !== vscode.DiagnosticSeverity.Error &&
                diag.severity !== vscode.DiagnosticSeverity.Warning
            ) {
                continue;
            }

            const errorLine = diag.range.start.line + 1;
            const cleanMessage = Sanitizer.sanitizeText(diag.message);
            const diagKey = `${filePath}:${errorLine}:${cleanMessage}`;
            currentUriDiags.add(diagKey);

            if (!this.activeDiagnostics.has(diagKey)) {
                // New Error Detected!
                this.activeDiagnostics.add(diagKey);

                const severityStr: 'error' | 'warning' | 'info' =
                    diag.severity === vscode.DiagnosticSeverity.Error ? 'error' : 'warning';

                const doc = vscode.workspace.textDocuments.find(
                    (d) => d.uri.toString() === uri.toString()
                );
                const language = doc ? doc.languageId : 'plaintext';

                const payload: ErrorDetectedPayload = {
                    file_path: filePath,
                    language,
                    error_message: cleanMessage,
                    error_line: errorLine,
                    severity: severityStr,
                    source: diag.source || 'compiler',
                };
                this.emitEvent('error_detected', payload);
            }
        }

        // Check for resolved errors on this file
        for (const key of Array.from(this.activeDiagnostics)) {
            if (key.startsWith(`${filePath}:`) && !currentUriDiags.has(key)) {
                // Error has been resolved!
                this.activeDiagnostics.delete(key);
                const parts = key.split(':');
                const line = parseInt(parts[1], 10) || 1;
                const msg = parts.slice(2).join(':');

                const payload: ErrorResolvedPayload = {
                    file_path: filePath,
                    language: 'plaintext',
                    error_message: msg,
                    error_line: line,
                };
                this.emitEvent('error_resolved', payload);
            }
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
