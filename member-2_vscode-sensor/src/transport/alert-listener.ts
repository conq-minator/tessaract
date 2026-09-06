/**
 * Alert Listener for VS Code Extension:
 * Listens to Member 4 Core Engine's alert stream on ws://127.0.0.1:9700/alerts
 * and displays interactive VS Code notifications with AI hints when friction is high.
 */

import WebSocket from 'ws';
import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
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
    private dismissedRuns: Set<string> = new Set();
    private conversationHistory: Array<{ role: 'user' | 'assistant'; content: string }> = [];

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
            const topic = (payload.topic as string) || 'your code';
            const errorMessage = typeof payload.error_message === 'string' ? payload.error_message : '';
            const errorLine = typeof payload.error_line === 'number' ? payload.error_line : undefined;
            const filePath = typeof payload.file_path === 'string' ? payload.file_path : undefined;
            let codeSnippet = typeof payload.code_snippet === 'string' ? payload.code_snippet : '';

            const runId = (payload.run_id as string) || `${topic}_${errorMessage}_${errorLine || ''}`;
            if (this.dismissedRuns.has(runId)) {
                return; // Already notified or dismissed for this run, do not spam
            }

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

            this.showInteractiveHintPrompt(runId, topic, this.lastContext);
        }
    }

    private showInteractiveHintPrompt(
        runId: string,
        topic: string,
        ctx: ActiveContext | null = null
    ): void {
        const filePath = ctx?.filePath;
        const errorLine = ctx?.errorLine;
        const fileBasename = filePath ? filePath.split(/[\\/]/).pop() : '';
        const locStr = fileBasename ? ` (${fileBasename}${errorLine ? `:${errorLine}` : ''})` : '';

        // Reset conversation history for new error episode
        this.conversationHistory = [];

        const message = `Tesseract: Error detected in ${topic}${locStr}. Would you like assistance?`;

        vscode.window.showWarningMessage(
            message,
            '💡 Hint (L1)',
            '🔍 Explain Error',
            '💬 Ask Question',
            'Dismiss'
        ).then(async (selection) => {
            // Mark this error run as dismissed/handled so it doesn't pop up again while idle
            this.dismissedRuns.add(runId);

            if (selection === '💡 Hint (L1)') {
                await this.fetchAndShowHint(topic, 1, ctx);
            } else if (selection === '🔍 Explain Error') {
                await this.fetchAndExplainError(ctx);
            } else if (selection === '💬 Ask Question') {
                await this.promptUserQuestion(ctx);
            }
        });
    }

    private async resolveContext(ctx: ActiveContext | null): Promise<{
        topic: string;
        errorMsg: string;
        errorLine?: number;
        filePath?: string;
        codeSnippet: string;
    }> {
        const activeCtx = ctx || this.lastContext;
        let topic = activeCtx?.topic || 'general';
        let errorMsg = activeCtx?.errorMessage || '';
        let errorLine = activeCtx?.errorLine;
        let filePath = activeCtx?.filePath;
        let codeSnippet = activeCtx?.codeSnippet || '';

        const activeEditor = vscode.window.activeTextEditor;
        const wsFolder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

        // 1. Resolve active editor document dynamically for any file
        if (activeEditor) {
            const activeFsPath = activeEditor.document.uri.fsPath;
            if (!filePath || filePath.endsWith(path.basename(activeFsPath))) {
                filePath = activeFsPath;
            }
            if (topic === 'general' || topic === 'your code') {
                topic = activeEditor.document.languageId;
            }
        }

        if (filePath && !path.isAbsolute(filePath) && wsFolder) {
            filePath = path.resolve(wsFolder, filePath);
        }

        // 2. Dynamically extract code snippet from active editor or filesystem
        if (!codeSnippet) {
            if (activeEditor) {
                codeSnippet = activeEditor.document.getText().slice(0, 1500);
            } else if (filePath && fs.existsSync(filePath)) {
                try {
                    codeSnippet = fs.readFileSync(filePath, 'utf8').slice(0, 1500);
                } catch {}
            }
        }

        // 3. Dry-run file dynamically to capture real runtime/syntax error if errorMsg is generic
        const isGenericError = !errorMsg ||
            errorMsg.startsWith('python') ||
            errorMsg.startsWith('node') ||
            errorMsg.includes('Runtime error') ||
            errorMsg.includes("can't open file") ||
            errorMsg === 'SyntaxError: invalid syntax';

        if (isGenericError && filePath && fs.existsSync(filePath)) {
            const isPy = filePath.endsWith('.py');
            const isJs = filePath.endsWith('.js') || filePath.endsWith('.ts');
            if (isPy || isJs) {
                const fileDir = path.dirname(filePath);
                const cmd = isPy ? `python "${filePath}"` : `node "${filePath}"`;
                try {
                    const output = await new Promise<string>((resolve) => {
                        cp.exec(cmd, { cwd: fileDir || wsFolder, timeout: 2500 }, (err, stdout, stderr) => {
                            resolve((stderr || stdout || err?.message || '').trim());
                        });
                    });
                    if (output && !output.includes("can't open file") && !output.includes("No such file")) {
                        const lines = output.split('\n').map(l => l.trim()).filter(Boolean);
                        if (lines.length > 0) {
                            errorMsg = lines[lines.length - 1];
                        }
                        const lineMatch = output.match(/line (\d+)/i);
                        if (lineMatch) {
                            errorLine = parseInt(lineMatch[1], 10);
                        }
                    }
                } catch {}
            }
        }

        // 4. Strip any leaked "can't open file" runner noise from errorMsg
        if (errorMsg.includes("can't open file") || errorMsg.includes("No such file")) {
            errorMsg = `Syntax or runtime error in ${topic}`;
        }

        return { topic, errorMsg, errorLine, filePath, codeSnippet };
    }

    private async promptUserQuestion(ctx: ActiveContext | null): Promise<void> {
        const resolved = await this.resolveContext(ctx);
        const { topic, errorMsg, codeSnippet } = resolved;

        const userPrompt = await vscode.window.showInputBox({
            title: `💬 Tesseract AI Tutor (${topic})`,
            prompt: 'Ask anything about your code, the error, or concept:',
            placeHolder: 'e.g. Why does this loop fail? or What concept does this use?',
            ignoreFocusOut: true
        });

        if (!userPrompt || !userPrompt.trim()) return;

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
                    history: this.conversationHistory
                });

                const answer = (res.answer as string) || (res.explanation as string) || (res.hint as string) || (res.message as string) || 'No response from tutor model.';
                
                // Track conversation turns so follow-ups retain context
                this.conversationHistory.push({ role: 'user', content: userPrompt.trim() });
                this.conversationHistory.push({ role: 'assistant', content: answer });

                vscode.window.showInformationMessage(
                    `🤖 Tesseract Tutor:\n\n${answer}`,
                    { modal: true },
                    '💬 Ask Follow-up',
                    '🔍 Explain Error',
                    'Close'
                ).then(async (sel) => {
                    if (sel === '💬 Ask Follow-up') {
                        await this.promptUserQuestion(resolved);
                    } else if (sel === '🔍 Explain Error') {
                        await this.fetchAndExplainError(resolved);
                    }
                });
            } catch (e: unknown) {
                const err = e instanceof Error ? e.message : String(e);
                vscode.window.showErrorMessage(`Tutor request failed: ${err}`);
            }
        });
    }

    private async fetchAndExplainError(ctx: ActiveContext | null): Promise<void> {
        const resolved = await this.resolveContext(ctx);
        const { topic, errorMsg, codeSnippet } = resolved;
        const updatedCtx: ActiveContext = { ...resolved, errorMessage: errorMsg };

        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `Tesseract: Analyzing runtime error with pedagogical model...`,
            cancellable: false
        }, async () => {
            try {
                const res = await this.requestAI('/api/v1/tutor/explain-error', {
                    topic,
                    error: errorMsg || `Runtime error in ${topic}`,
                    code: codeSnippet || ''
                });

                const explanation = (res.explanation as string) || (res.answer as string) || (res.hint as string) || (res.message as string) || 'No error details found.';

                vscode.window.showInformationMessage(
                    explanation,
                    { modal: true },
                    '💡 Start Hints (L1)',
                    '💬 Ask Question',
                    'Close'
                ).then(async (sel) => {
                    if (sel === '💡 Start Hints (L1)') {
                        await this.fetchAndShowHint(topic, 1, updatedCtx);
                    } else if (sel === '💬 Ask Question') {
                        await this.promptUserQuestion(updatedCtx);
                    }
                });
            } catch (e: unknown) {
                const err = e instanceof Error ? e.message : String(e);
                vscode.window.showErrorMessage(`Failed to explain error: ${err}`);
            }
        });
    }

    private async fetchAndShowHint(topic: string, level: number = 1, ctx: ActiveContext | null = null): Promise<void> {
        const resolved = await this.resolveContext(ctx);
        const detectedTopic = topic || resolved.topic || 'python';
        const errorMsg = resolved.errorMsg;
        const errorLine = resolved.errorLine;
        const filePath = resolved.filePath;
        const codeSnippet = resolved.codeSnippet;
        const updatedCtx: ActiveContext = { ...resolved, topic: detectedTopic, errorMessage: errorMsg };

        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `Tesseract: Analyzing code & fetching Level ${level} hint...`,
            cancellable: false
        }, async () => {
            try {
                let contextStr = `Language: ${detectedTopic}`;
                if (errorMsg) {
                    contextStr += `\nError: ${errorMsg}`;
                }
                if (errorLine) {
                    contextStr += `\nLine: ${errorLine}`;
                }
                if (codeSnippet) {
                    contextStr += `\nCode Context:\n${codeSnippet}`;
                }

                const hintData = await this.requestAI('/api/v1/tutor/hint', {
                    topic: detectedTopic,
                    level,
                    code: codeSnippet,
                    error: errorMsg,
                    context: contextStr
                });

                const hintText = (hintData.hint as string) || (hintData.content as string) || (hintData.explanation as string) || (hintData.message as string) || 'Check your syntax and variable types.';
                const nextLevel = level + 1;
                const nextBtn = nextLevel <= 3 ? `💡 Next Hint (L${nextLevel})` : undefined;

                const buttons: string[] = [];
                if (nextBtn) buttons.push(nextBtn);
                buttons.push('🔍 Explain Error', '💬 Ask Question', 'Close');

                const levelNames: Record<number, string> = {1: 'Nudge', 2: 'Concept', 3: 'Strategy'};
                const levelLabel = levelNames[level] || 'Hint';

                vscode.window.showInformationMessage(
                    `💡 Level ${level} ${levelLabel} (${detectedTopic}):\n\n${hintText}`,
                    { modal: true },
                    ...buttons
                ).then(async (nextSel) => {
                    const updatedCtx: ActiveContext = {
                        topic: detectedTopic,
                        errorMessage: errorMsg,
                        errorLine,
                        filePath,
                        codeSnippet
                    };
                    if (nextSel === nextBtn && nextLevel <= 3) {
                        await this.fetchAndShowHint(detectedTopic, nextLevel, updatedCtx);
                    } else if (nextSel === '🔍 Explain Error') {
                        await this.fetchAndExplainError(updatedCtx);
                    } else if (nextSel === '💬 Ask Question') {
                        await this.promptUserQuestion(updatedCtx);
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
