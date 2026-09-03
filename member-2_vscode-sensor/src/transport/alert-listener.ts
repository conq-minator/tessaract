/**
 * Alert Listener for VS Code Extension:
 * Listens to Member 4 Core Engine's alert stream on ws://127.0.0.1:9700/alerts
 * and displays interactive VS Code notifications with AI hints when friction is high.
 */

import WebSocket from 'ws';
import * as vscode from 'vscode';
import http from 'http';
import { Logger } from '../utils/logger';

export class AlertListener {
    private ws: WebSocket | null = null;
    private url: string;
    private secret: string;
    private isPaused: boolean = false;
    private reconnectTimer: NodeJS.Timeout | null = null;
    private lastAlertTime: number = 0;

    constructor(url: string = 'ws://127.0.0.1:9700/alerts', secret: string = '') {
        this.url = url;
        this.secret = secret;
    }

    public connect(): void {
        if (this.isPaused) return;

        try {
            const headers: Record<string, string> = {};
            let connectUrl = this.url;
            if (this.secret) {
                headers['Authorization'] = `Bearer ${this.secret}`;
                const separator = connectUrl.includes('?') ? '&' : '?';
                connectUrl = `${connectUrl}${separator}token=${encodeURIComponent(this.secret)}`;
            }

            this.ws = new WebSocket(connectUrl, { headers });

            this.ws.on('open', () => {
                Logger.info('AlertListener connected to Core Engine alert stream.');
            });

            this.ws.on('message', (data: WebSocket.Data) => {
                try {
                    const message = JSON.parse(data.toString());
                    this.handleAlert(message);
                } catch (e) {
                    Logger.error('Failed to parse alert message:', e);
                }
            });

            this.ws.on('close', () => {
                this.scheduleReconnect();
            });

            this.ws.on('error', (err) => {
                Logger.warn(`AlertListener error: ${err.message}`);
            });
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : String(err);
            Logger.error(`AlertListener connection exception: ${message}`);
            this.scheduleReconnect();
        }
    }

    private handleAlert(alert: { type?: string; alert_type?: string; payload?: Record<string, unknown> }): void {
        const alertType = alert.alert_type || alert.type;
        const payload = alert.payload || {};

        Logger.info(`Received alert stream message: ${alertType}`);

        if (alertType === 'stuck_detected' || alertType === 'friction_alert') {
            // Rate limit popups to once every 60 seconds
            const now = Date.now();
            if (now - this.lastAlertTime < 60000) return;
            this.lastAlertTime = now;

            const topic = (payload.topic as string) || 'your code';
            const frictionScore = typeof payload.friction_score === 'number' 
                ? (payload.friction_score as number).toFixed(2) 
                : 'High';
            const pregenHint = typeof payload.hint === 'string' ? payload.hint : '';
            this.showInteractiveHintPrompt(topic, frictionScore, pregenHint);
        }
    }

    private showInteractiveHintPrompt(topic: string, frictionScore: string, pregenHint: string = ''): void {
        const message = pregenHint 
            ? `💡 Tesseract AI Hint (${topic}): ${pregenHint}`
            : `💡 Tesseract Copilot: High friction (${frictionScore}) detected in ${topic}!`;
        
        vscode.window.showWarningMessage(
            message,
            '📖 Explain Concept',
            '💡 Next Hint (L2)',
            'Dismiss'
        ).then(async (selection) => {
            if (selection === '📖 Explain Concept') {
                await this.fetchAndShowExplanation(topic);
            } else if (selection === '💡 Next Hint (L2)') {
                await this.fetchAndShowHint(topic, 2);
            }
        });
    }

    private async fetchAndShowHint(topic: string, level: number = 1): Promise<void> {
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `Tesseract: Fetching Level ${level} hint for ${topic}...`,
            cancellable: false
        }, async () => {
            try {
                const hintData = await this.requestAI('/api/v1/tutor/hint', {
                    topic,
                    level,
                    context: `User is debugging in editor with syntax/runtime errors in ${topic}`
                });

                const hintText = hintData.hint || hintData.message || 'Check your syntax and variable types on the line indicated by the error.';
                
                vscode.window.showInformationMessage(
                    `💡 Hint (${topic}): ${hintText}`,
                    'Next Hint (L2)',
                    'Close'
                ).then(async (nextSel) => {
                    if (nextSel === 'Next Hint (L2)') {
                        const l2Data = await this.requestAI('/api/v1/tutor/hint', {
                            topic,
                            level: 2,
                            context: 'User requested Level 2 hint'
                        });
                        vscode.window.showInformationMessage(`💡 Level 2 Hint: ${l2Data.hint || l2Data.message}`);
                    }
                });
            } catch (e: unknown) {
                const err = e instanceof Error ? e.message : String(e);
                vscode.window.showErrorMessage(`Failed to fetch hint: ${err}`);
            }
        });
    }

    private async fetchAndShowExplanation(topic: string): Promise<void> {
        try {
            const data = await this.requestAI('/api/v1/tutor/explain', {
                concept: topic,
                user_level: 'beginner',
                context: 'User requested explanation from editor popup'
            });

            const explanation = data.explanation || data.content || `Explanation for ${topic}`;
            const doc = await vscode.workspace.openTextDocument({
                content: `# Tesseract AI Explanation: ${topic}\n\n${explanation}`,
                language: 'markdown'
            });
            await vscode.window.showTextDocument(doc, { preview: true, viewColumn: vscode.ViewColumn.Beside });
        } catch (e: unknown) {
            const err = e instanceof Error ? e.message : String(e);
            vscode.window.showErrorMessage(`Failed to fetch explanation: ${err}`);
        }
    }

    private requestAI(endpoint: string, body: Record<string, unknown>): Promise<Record<string, unknown>> {
        return new Promise((resolve, reject) => {
            const postData = JSON.stringify(body);
            const req = http.request({
                hostname: '127.0.0.1',
                port: 9701,
                path: endpoint,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(postData),
                    'Authorization': `Bearer ${this.secret || 'rQUSMHvr5MVgVdCH-b8seB7UbRYeykyJYjBzaZeN2Pk'}`
                },
                timeout: 8000
            }, (res) => {
                let responseData = '';
                res.on('data', (chunk) => { responseData += chunk; });
                res.on('end', () => {
                    try {
                        const json = JSON.parse(responseData);
                        resolve(json);
                    } catch (err) {
                        resolve({ hint: responseData });
                    }
                });
            });

            req.on('error', (err) => {
                // Fallback structured hint if Member 5 request times out
                resolve({
                    hint: `Double check loop syntax and ensure you are iterating cleanly over items (e.g. for item in list:).`
                });
            });

            req.on('timeout', () => {
                req.destroy();
                resolve({
                    hint: `Double check loop syntax and ensure you are iterating cleanly over items (e.g. for item in list:).`
                });
            });

            req.write(postData);
            req.end();
        });
    }

    private scheduleReconnect(): void {
        if (this.isPaused || this.reconnectTimer) return;
        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
        }, 5000);
    }

    public disconnect(): void {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        if (this.ws) {
            this.ws.removeAllListeners();
            this.ws.close();
            this.ws = null;
        }
    }
}
