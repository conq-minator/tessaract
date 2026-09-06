/**
 * Terminal Monitor: Observes command execution and process exit codes.
 */

import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
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

                    // Fallback to extract file path directly from terminal command if editor was blurred/unfocused
                    if (!detectedFilePath) {
                        const cmdFileMatch = cleanCommand.match(/(?:python|node)\s+(?:"([^"]+)"|'([^']+)'|(\S+))/i);
                        if (cmdFileMatch) {
                            detectedFilePath = cmdFileMatch[1] || cmdFileMatch[2] || cmdFileMatch[3];
                        }
                    }

                    const payload: TerminalCommandPayload & { file_path?: string; language?: string; topic?: string } = {
                        command: cleanCommand,
                        exit_code: e.exitCode,
                        file_path: detectedFilePath,
                        language: detectedLang,
                        topic: detectedLang
                    };
                    this.emitEvent('terminal_command', payload);

                    const wsFolder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
                    const realPath = (activeDoc && activeDoc.uri.fsPath) ? activeDoc.uri.fsPath :
                                     (detectedFilePath && wsFolder ? path.resolve(wsFolder, detectedFilePath) : detectedFilePath);

                    // 1. If terminal command failed, capture the exact runtime error & code snippet
                    if (e.exitCode !== undefined && e.exitCode !== 0 && realPath) {
                        const execCmd = detectedLang === 'python' ? `python "${realPath}"` :
                                        detectedLang === 'javascript' ? `node "${realPath}"` : cleanCommand;

                        cp.exec(execCmd, { cwd: wsFolder, timeout: 2500 }, (err, stdout, stderr) => {
                            const combined = (stderr || stdout || err?.message || '').trim();
                            if (!combined || combined.includes("can't open file") || combined.includes("No such file")) return;

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
                            if (activeDoc && activeDoc.uri.fsPath === realPath) {
                                const docLines = activeDoc.getText().split('\n');
                                if (errorLine && errorLine > 0 && errorLine <= docLines.length) {
                                    const start = Math.max(0, errorLine - 4);
                                    const end = Math.min(docLines.length, errorLine + 3);
                                    snippet = docLines.slice(start, end).join('\n');
                                } else {
                                    snippet = docLines.slice(0, 25).join('\n');
                                }
                            } else if (fs.existsSync(realPath)) {
                                try {
                                    snippet = fs.readFileSync(realPath, 'utf8').slice(0, 1000);
                                } catch {}
                            }

                            this.emitEvent('error_detected', {
                                file_path: realPath,
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
                    } else if (e.exitCode === 0 && realPath) {
                        // 2. If command exited cleanly (exit code 0), check for silent logical bugs (e.g. empty range)
                        let codeContent = '';
                        if (activeDoc && activeDoc.uri.fsPath === realPath) {
                            codeContent = activeDoc.getText();
                        } else if (fs.existsSync(realPath)) {
                            try {
                                codeContent = fs.readFileSync(realPath, 'utf8');
                            } catch {}
                        }

                        if (codeContent && (detectedLang === 'python' || detectedLang === 'javascript')) {
                            const silentBug = this.detectSilentLogicBug(codeContent, detectedLang);
                            if (silentBug) {
                                this.emitEvent('error_detected', {
                                    file_path: realPath,
                                    language: detectedLang,
                                    topic: detectedLang,
                                    error_message: silentBug.message,
                                    error_line: silentBug.line,
                                    code_snippet: silentBug.snippet || codeContent.slice(0, 500),
                                    full_traceback: silentBug.message,
                                    severity: 'warning',
                                    source: 'logical_analysis'
                                });
                            }
                        }
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

    private detectSilentLogicBug(code: string, language: string): { message: string; line: number; snippet?: string } | null {
        const lines = code.split('\n');

        if (language === 'python') {
            const rangeRegex = /\brange\s*\(\s*(-?\d+)\s*,\s*(-?\d+)(?:\s*,\s*(-?\d+))?\s*\)/;
            for (let idx = 0; idx < lines.length; idx++) {
                const line = lines[idx];
                const trimmed = line.trim();
                if (trimmed.startsWith('#')) continue;

                const m = line.match(rangeRegex);
                if (m) {
                    const start = parseInt(m[1], 10);
                    const stop = parseInt(m[2], 10);
                    const step = m[3] !== undefined ? parseInt(m[3], 10) : 1;

                    if (step > 0 && start > stop) {
                        const stepDesc = m[3] !== undefined ? `step (${step})` : 'default step (+1)';
                        return {
                            message: `LogicalWarning on line ${idx + 1}: range(${start}, ${stop}) creates an empty sequence because start (${start}) > stop (${stop}) with ${stepDesc}. The loop body will never execute.`,
                            line: idx + 1,
                            snippet: line.trim()
                        };
                    } else if (step < 0 && start < stop) {
                        return {
                            message: `LogicalWarning on line ${idx + 1}: range(${start}, ${stop}, ${step}) creates an empty sequence because start (${start}) < stop (${stop}) with negative step (${step}). The loop body will never execute.`,
                            line: idx + 1,
                            snippet: line.trim()
                        };
                    }
                }
            }
        } else if (language === 'javascript' || language === 'typescript') {
            const jsForRegex = /\bfor\s*\(\s*(?:let|var)\s+\w+\s*=\s*(\d+)\s*;\s*\w+\s*(<|<=|>|>=)\s*(\d+)\s*;\s*\w+(\+\+|--|\+=|-=)/;
            for (let idx = 0; idx < lines.length; idx++) {
                const line = lines[idx];
                const trimmed = line.trim();
                if (trimmed.startsWith('//')) continue;

                const m = line.match(jsForRegex);
                if (m) {
                    const initVal = parseInt(m[1], 10);
                    const op = m[2];
                    const limitVal = parseInt(m[3], 10);
                    if ((op === '<' || op === '<=') && initVal >= limitVal) {
                        return {
                            message: `LogicalWarning on line ${idx + 1}: Loop condition '${initVal} ${op} ${limitVal}' evaluates to false immediately. The loop body will never execute.`,
                            line: idx + 1,
                            snippet: line.trim()
                        };
                    } else if ((op === '>' || op === '>=') && initVal <= limitVal) {
                        return {
                            message: `LogicalWarning on line ${idx + 1}: Loop condition '${initVal} ${op} ${limitVal}' evaluates to false immediately. The loop body will never execute.`,
                            line: idx + 1,
                            snippet: line.trim()
                        };
                    }
                }
            }
        }

        return null;
    }
}
