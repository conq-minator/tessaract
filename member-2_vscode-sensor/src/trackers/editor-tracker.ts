/**
 * Editor Activity Tracker: Observes file opens, closes, saves, and debounced edits.
 */

import * as vscode from 'vscode';
import { v4 as uuidv4 } from 'uuid';
import { WebSocketClient } from '../transport/websocket-client';
import { SessionManager } from '../utils/session-manager';
import { Sanitizer } from '../utils/sanitizer';
import {
    FileOpenedPayload,
    FileSavedPayload,
    FileClosedPayload,
    FileEditedPayload,
    TesseractEvent,
} from '../types/events';

export class EditorTracker {
    private client: WebSocketClient;
    private sessionMgr: SessionManager;
    private fileOpenTimes: Map<string, number> = new Map();
    private editDebounceTimers: Map<string, NodeJS.Timeout> = new Map();
    private editChangeCounters: Map<string, number> = new Map();
    private debounceMs: number;

    constructor(client: WebSocketClient, debounceMs: number = 2000) {
        this.client = client;
        this.sessionMgr = SessionManager.getInstance();
        this.debounceMs = debounceMs;
    }

    public register(context: vscode.ExtensionContext): void {
        // 1. File Opened
        context.subscriptions.push(
            vscode.workspace.onDidOpenTextDocument((doc) => {
                if (this.shouldIgnore(doc)) return;
                const filePath = Sanitizer.formatFilePath(doc.uri);
                this.fileOpenTimes.set(filePath, Date.now());

                const payload: FileOpenedPayload = {
                    file_path: filePath,
                    language: doc.languageId,
                    workspace: vscode.workspace.name,
                };
                this.emitEvent('file_opened', payload);
            })
        );

        // 2. File Saved
        context.subscriptions.push(
            vscode.workspace.onDidSaveTextDocument((doc) => {
                if (this.shouldIgnore(doc)) return;
                const filePath = Sanitizer.formatFilePath(doc.uri);

                const payload: FileSavedPayload = {
                    file_path: filePath,
                    language: doc.languageId,
                    change_size: doc.getText().length,
                    line_count: doc.lineCount,
                };
                this.emitEvent('file_saved', payload);
            })
        );

        // 3. File Closed
        context.subscriptions.push(
            vscode.workspace.onDidCloseTextDocument((doc) => {
                if (this.shouldIgnore(doc)) return;
                const filePath = Sanitizer.formatFilePath(doc.uri);
                const openTime = this.fileOpenTimes.get(filePath) || Date.now();
                this.fileOpenTimes.delete(filePath);

                const payload: FileClosedPayload = {
                    file_path: filePath,
                    language: doc.languageId,
                    duration_ms: Date.now() - openTime,
                };
                this.emitEvent('file_closed', payload);
            })
        );

        // 4. Debounced File Edits
        context.subscriptions.push(
            vscode.workspace.onDidChangeTextDocument((e) => {
                if (this.shouldIgnore(e.document)) return;
                const filePath = Sanitizer.formatFilePath(e.document.uri);

                // Accumulate changes
                let charsChanged = 0;
                for (const change of e.contentChanges) {
                    charsChanged += change.text.length;
                }
                const currentCount = this.editChangeCounters.get(filePath) || 0;
                this.editChangeCounters.set(filePath, currentCount + charsChanged);

                // Clear previous debounce timer
                const existingTimer = this.editDebounceTimers.get(filePath);
                if (existingTimer) {
                    clearTimeout(existingTimer);
                }

                // Schedule debounced emission
                const timer = setTimeout(() => {
                    const totalChars = this.editChangeCounters.get(filePath) || 0;
                    this.editChangeCounters.delete(filePath);
                    this.editDebounceTimers.delete(filePath);

                    const payload: FileEditedPayload = {
                        file_path: filePath,
                        language: e.document.languageId,
                        line_count: e.document.lineCount,
                        change_character_count: totalChars,
                    };
                    this.emitEvent('file_edited', payload);
                }, this.debounceMs);

                this.editDebounceTimers.set(filePath, timer);
            })
        );
    }

    private shouldIgnore(doc: vscode.TextDocument): boolean {
        return (
            doc.uri.scheme !== 'file' ||
            doc.fileName.includes('.git') ||
            doc.fileName.includes('node_modules') ||
            doc.fileName.endsWith('.log')
        );
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
