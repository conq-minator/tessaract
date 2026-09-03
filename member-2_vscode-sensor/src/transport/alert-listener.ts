/**
 * Alert Listener for VS Code Extension:
 * Listens to Member 4 Core Engine's alert stream on ws://127.0.0.1:9700/alerts
 * and displays interactive VS Code notifications with AI hints when friction is high.
 */

import WebSocket from 'ws';
import * as vscode from 'vscode';
import * as cp from 'child_process';
import http from 'http';
import { Logger } from '../utils/logger';

interface ActiveContext {
    topic: string;
    errorMessage?: string;
    errorLine?: number;
    filePath?: string;
    codeSnippet?: string;
}

export class AlertListener {
    private url: string;
    private ws: WebSocket | null = null;
    private secret: string;
    private isPaused: boolean = false;
    private reconnectTimer: NodeJS.Timeout | null = null;
    private lastAlertTime: number = 0;
    private lastContext: ActiveContext | null = null;

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
                    Logger.error('Failed to parse incoming alert:', e);
                }
            });

            this.ws.on('close', () => {
                Logger.warn('AlertListener websocket connection closed.');
                this.scheduleReconnect();
            });

            this.ws.on('error', (err) => {
                Logger.error('AlertListener websocket error:', err);
            });
        } catch (e) {
            Logger.error('Failed to initialize AlertListener websocket:', e);
            this.scheduleReconnect();
        }
    }

    private handleAlert(alert: { type: string; payload: Record<string, unknown> }): void {
        const alertType = alert.type;
        const payload = alert.payload || {};

        Logger.info(`Received alert stream message: ${alertType}`);

        if (alertType === 'stuck_detected' || alertType === 'friction_alert') {
            // Rate limit popups to once every 15 seconds
            const now = Date.now();
            if (now - this.lastAlertTime < 15000) return;
            this.lastAlertTime = now;

            const topic = (payload.topic as string) || 'your code';
            const frictionScore = typeof payload.friction_score === 'number' 
                ? (payload.friction_score as number).toFixed(2) 
                : 'High';
            const pregenHint = typeof payload.hint === 'string' ? payload.hint : '';
            const errorMessage = typeof payload.error_message === 'string' ? payload.error_message : '';
            const errorLine = typeof payload.error_line === 'number' ? payload.error_line : undefined;
            const filePath = typeof payload.file_path === 'string' ? payload.file_path : undefined;
            let codeSnippet = typeof payload.code_snippet === 'string' ? payload.code_snippet : '';

            // Extract snippet from active text editor if missing
            if (!codeSnippet && vscode.window.activeTextEditor) {
                const doc = vscode.window.activeTextEditor.document;
                const docLines = doc.getText().split('\n');
                if (errorLine && errorLine > 0 && errorLine <= docLines.length) {
                    const s = Math.max(0, errorLine - 4);
                    const e = Math.min(docLines.length, errorLine + 3);
                    codeSnippet = docLines.slice(s, e).join('\n');
                } else {
                    codeSnippet = docLines.slice(0, 30).join('\n');
                }
            }

            this.lastContext = {
                topic,
                errorMessage,
                errorLine,
                filePath,
                codeSnippet
            };

            this.showInteractiveHintPrompt(topic, frictionScore, pregenHint, this.lastContext);
        }
    }

    private showInteractiveHintPrompt(
        topic: string,
        frictionScore: string,
        pregenHint: string = '',
        ctx: ActiveContext | null = null
    ): void {
        const message = pregenHint 
            ? `💡 Tesseract AI Hint (${topic}): ${pregenHint}`
            : `💡 Tesseract Copilot: High friction (${frictionScore}) detected in ${topic}!`;
        
        vscode.window.showWarningMessage(
            message,
            '💬 Ask Question',
            '🔍 Explain Error',
            '💡 Next Hint (L2)',
            'Dismiss'
        ).then(async (selection) => {
            if (selection === '💬 Ask Question') {
                await this.promptUserQuestion(ctx);
            } else if (selection === '🔍 Explain Error') {
                await this.fetchAndExplainError(ctx);
            } else if (selection === '💡 Next Hint (L2)') {
                await this.fetchAndShowHint(topic, 2, ctx);
            }
        });
    }

    private async promptUserQuestion(ctx: ActiveContext | null): Promise<void> {
        let topic = ctx?.topic || 'general';
        let errorMsg = ctx?.errorMessage || '';
        let filePath = ctx?.filePath;
        let codeSnippet = ctx?.codeSnippet;

        const activeEditor = vscode.window.activeTextEditor;
        if (activeEditor) {
            filePath = filePath || activeEditor.document.uri.fsPath;
            if (topic === 'general' || topic === 'your code') {
                topic = activeEditor.document.languageId;
            }
        }

        const userPrompt = await vscode.window.showInputBox({
            title: `💬 Tesseract AI Tutor (${topic})`,
            prompt: 'Ask anything about your code, the error, or concept:',
            placeHolder: 'e.g. Why does total += num crash here? or How do I fix line 7?',
            ignoreFocusOut: true
        });

        if (!userPrompt || !userPrompt.trim()) return;

        // If errorMsg is missing or generic, run a quick dry-run to get the real error
        if (!errorMsg || errorMsg.startsWith('python') || errorMsg.startsWith('node') || errorMsg.includes('Runtime error')) {
            if (filePath && (filePath.endsWith('.py') || filePath.endsWith('.js'))) {
                const cmd = filePath.endsWith('.py') ? `python "${filePath}"` : `node "${filePath}"`;
                try {
                    const output = await new Promise<string>((resolve) => {
                        cp.exec(cmd, { timeout: 2500 }, (err, stdout, stderr) => {
                            resolve((stderr || stdout || err?.message || '').trim());
                        });
                    });
                    if (output) {
                        const lines = output.split('\n').map(l => l.trim()).filter(Boolean);
                        errorMsg = lines[lines.length - 1];
                    }
                } catch {}
            }
        }

        if (!codeSnippet && activeEditor) {
            codeSnippet = activeEditor.document.getText().slice(0, 1000);
        }

        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `Tesseract: Asking tutor model about your question...`,
            cancellable: false
        }, async () => {
            try {
                const res = await this.requestAI('/api/v1/tutor/ask', {
                    question: userPrompt.trim(),
                    topic,
                    error: errorMsg || '',
                    code: codeSnippet || '',
                    file_path: filePath || ''
                });

                const answer = (res.answer as string) || (res.explanation as string) || (res.hint as string) || (res.message as string) || 'No response from tutor model.';
                
                vscode.window.showInformationMessage(
                    `🤖 Tesseract Tutor:\n\n${answer}`,
                    { modal: true },
                    '💬 Ask Follow-up',
                    '🔍 Explain Error',
                    'Close'
                ).then(async (sel) => {
                    if (sel === '💬 Ask Follow-up') {
                        await this.promptUserQuestion(ctx);
                    } else if (sel === '🔍 Explain Error') {
                        await this.fetchAndExplainError(ctx);
                    }
                });
            } catch (e: unknown) {
                const err = e instanceof Error ? e.message : String(e);
                vscode.window.showErrorMessage(`Tutor request failed: ${err}`);
            }
        });
    }

    private async fetchAndExplainError(ctx: ActiveContext | null): Promise<void> {
        let topic = ctx?.topic || 'general';
        let errorMsg = ctx?.errorMessage || '';
        let filePath = ctx?.filePath;
        let codeSnippet = ctx?.codeSnippet;

        const activeEditor = vscode.window.activeTextEditor;
        if (activeEditor) {
            filePath = filePath || activeEditor.document.uri.fsPath;
            if (topic === 'general' || topic === 'your code') {
                topic = activeEditor.document.languageId;
            }
        }

        // If errorMsg is missing or generic, run a quick dry-run of the file to get the exact traceback!
        if (!errorMsg || errorMsg.startsWith('python') || errorMsg.startsWith('node') || errorMsg.includes('Runtime error')) {
            if (filePath && (filePath.endsWith('.py') || filePath.endsWith('.js'))) {
                const cmd = filePath.endsWith('.py') ? `python "${filePath}"` : `node "${filePath}"`;
                try {
                    const output = await new Promise<string>((resolve) => {
                        cp.exec(cmd, { timeout: 2500 }, (err, stdout, stderr) => {
                            resolve((stderr || stdout || err?.message || '').trim());
                        });
                    });
                    if (output) {
                        const lines = output.split('\n').map(l => l.trim()).filter(Boolean);
                        errorMsg = lines[lines.length - 1]; // e.g. "AssertionError: Expected 1 task, but got 2..."
                        const lineMatch = output.match(/line (\d+)/i);
                        if (lineMatch && activeEditor) {
                            const lineNo = parseInt(lineMatch[1], 10);
                            const docLines = activeEditor.document.getText().split('\n');
                            const s = Math.max(0, lineNo - 5);
                            const e = Math.min(docLines.length, lineNo + 4);
                            codeSnippet = docLines.slice(s, e).join('\n');
                        }
                    }
                } catch {}
            }
        }

        if (!codeSnippet && activeEditor) {
            codeSnippet = activeEditor.document.getText().slice(0, 1000);
        }

        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `Tesseract: Analyzing runtime error with pedagogical model...`,
            cancellable: false
        }, async () => {
            try {
                const res = await this.requestAI('/api/v1/tutor/explain-error', {
                    topic,
                    error: errorMsg || `Runtime error in ${topic}`,
                    code: codeSnippet || '',
                    file_path: filePath || ''
                });

                const explanation = (res.explanation as string) || (res.answer as string) || (res.hint as string) || (res.message as string) || 'No error details found.';

                vscode.window.showInformationMessage(
                    explanation,
                    { modal: true },
                    '💬 Ask Question',
                    '💡 Next Hint (L2)',
                    'Close'
                ).then(async (sel) => {
                    if (sel === '💬 Ask Question') {
                        await this.promptUserQuestion(ctx);
                    } else if (sel === '💡 Next Hint (L2)') {
                        await this.fetchAndShowHint(topic, 2, ctx);
                    }
                });
            } catch (e: unknown) {
                const err = e instanceof Error ? e.message : String(e);
                vscode.window.showErrorMessage(`Failed to explain error: ${err}`);
            }
        });
    }

    private async fetchAndShowHint(topic: string, level: number = 1, ctx: ActiveContext | null = null): Promise<void> {
        const activeCtx = ctx || this.lastContext;
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `Tesseract: Fetching Level ${level} hint for ${topic}...`,
            cancellable: false
        }, async () => {
            try {
                let contextStr = `Language: ${topic}`;
                if (activeCtx?.errorMessage) {
                    contextStr += `\nError: ${activeCtx.errorMessage}`;
                }
                if (activeCtx?.errorLine) {
                    contextStr += `\nLine: ${activeCtx.errorLine}`;
                }
                if (activeCtx?.codeSnippet) {
                    contextStr += `\nCode Context:\n${activeCtx.codeSnippet}`;
                }

                const hintData = await this.requestAI('/api/v1/tutor/hint', {
                    topic,
                    level,
                    context: contextStr
                });

                const hintText = (hintData.hint as string) || (hintData.content as string) || (hintData.explanation as string) || (hintData.message as string) || 'Check your syntax and variable types.';
                const nextLevel = level + 1;
                const nextBtn = nextLevel <= 3 ? `💡 Next Hint (L${nextLevel})` : undefined;

                const buttons: string[] = [];
                if (nextBtn) buttons.push(nextBtn);
                buttons.push('🔍 Explain Error', '💬 Ask Question', 'Close');

                vscode.window.showInformationMessage(
                    `💡 Level ${level} Hint (${topic}):\n\n${hintText}`,
                    { modal: level >= 2 },
                    ...buttons
                ).then(async (nextSel) => {
                    if (nextSel === nextBtn && nextLevel <= 3) {
                        await this.fetchAndShowHint(topic, nextLevel, activeCtx);
                    } else if (nextSel === '🔍 Explain Error') {
                        await this.fetchAndExplainError(activeCtx);
                    } else if (nextSel === '💬 Ask Question') {
                        await this.promptUserQuestion(activeCtx);
                    }
                });
            } catch (e: unknown) {
                const err = e instanceof Error ? e.message : String(e);
                vscode.window.showErrorMessage(`Failed to fetch hint: ${err}`);
            }
        });
    }

    private requestAI(endpoint: string, body: Record<string, unknown>): Promise<Record<string, unknown>> {
        return new Promise((resolve) => {
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
                timeout: 60000
            }, (res) => {
                let responseData = '';
                res.on('data', (chunk) => { responseData += chunk; });
                res.on('end', () => {
                    try {
                        const json = JSON.parse(responseData);
                        resolve(json);
                    } catch (err) {
                        resolve({ hint: responseData, explanation: responseData, answer: responseData });
                    }
                });
            });

            req.on('error', (err) => {
                const msg = `Unable to connect to AI Tutor on 127.0.0.1:9701 (${err.message}).`;
                resolve({
                    hint: msg,
                    explanation: msg,
                    answer: msg
                });
            });

            req.on('timeout', () => {
                req.destroy();
                const msg = 'Model generation took over 35 seconds. Please try again.';
                resolve({
                    hint: msg,
                    explanation: msg,
                    answer: msg
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
