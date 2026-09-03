/**
 * Privacy Sanitizer: Redacts passwords, API keys, secrets, and formats file paths.
 */

import * as vscode from 'vscode';
import * as path from 'path';

export class Sanitizer {
    private static readonly SECRET_PATTERNS: RegExp[] = [
        /(?:password|passwd|pwd|secret|token|api_key|apikey|bearer)\s*[:=]\s*["']?([^"'\s]+)["']?/gi,
        /(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}/g, // GitHub tokens
        /sk-[A-Za-z0-9]{32,}/g, // OpenAI keys
        /AIza[0-9A-Za-z-_]{35}/g, // Google API keys
    ];

    public static sanitizeText(text: string): string {
        if (!text) return '';
        let sanitized = text;
        for (const pattern of this.SECRET_PATTERNS) {
            sanitized = sanitized.replace(pattern, '[REDACTED_SECRET]');
        }
        return sanitized;
    }

    public static formatFilePath(
        uri: vscode.Uri,
        strategy: 'relative' | 'full' | 'anonymized' = 'relative'
    ): string {
        const fullPath = uri.fsPath;

        if (strategy === 'full') {
            return fullPath;
        }

        if (strategy === 'anonymized') {
            const ext = path.extname(fullPath);
            return `file_${Math.abs(this.hashCode(fullPath))}${ext}`;
        }

        // Default 'relative'
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(uri);
        if (workspaceFolder) {
            return path.relative(workspaceFolder.uri.fsPath, fullPath).replace(/\\/g, '/');
        }

        return path.basename(fullPath);
    }

    private static hashCode(str: string): number {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = (hash << 5) - hash + char;
            hash |= 0;
        }
        return hash;
    }
}
