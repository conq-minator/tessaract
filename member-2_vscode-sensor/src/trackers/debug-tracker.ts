/**
 * Debug Tracker: Observes debug session lifecycles and breakpoints.
 */

import * as vscode from 'vscode';
import { v4 as uuidv4 } from 'uuid';
import { WebSocketClient } from '../transport/websocket-client';
import { SessionManager } from '../utils/session-manager';
import { DebugPayload, TesseractEvent } from '../types/events';

export class DebugTracker {
    private client: WebSocketClient;
    private sessionMgr: SessionManager;

    constructor(client: WebSocketClient) {
        this.client = client;
        this.sessionMgr = SessionManager.getInstance();
    }

    public register(context: vscode.ExtensionContext): void {
        // 1. Debug Session Started
        context.subscriptions.push(
            vscode.debug.onDidStartDebugSession((session) => {
                const payload: DebugPayload = {
                    session_name: session.name,
                    debug_type: session.type,
                };
                this.emitEvent('debug_started', payload);
            })
        );

        // 2. Debug Session Ended
        context.subscriptions.push(
            vscode.debug.onDidTerminateDebugSession((session) => {
                const payload: DebugPayload = {
                    session_name: session.name,
                    debug_type: session.type,
                };
                this.emitEvent('debug_ended', payload);
            })
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
