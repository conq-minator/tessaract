/**
 * Privacy-safe OutputChannel logger for Tesseract VS Code Sensor.
 */

import * as vscode from 'vscode';

export class Logger {
    private static channel: vscode.OutputChannel | null = null;

    public static initialize(context: vscode.ExtensionContext): void {
        if (!this.channel) {
            this.channel = vscode.window.createOutputChannel('Tesseract Sensor');
            context.subscriptions.push(this.channel);
        }
    }

    public static debug(message: string, ...args: unknown[]): void {
        this.log('DEBUG', message, ...args);
    }

    public static info(message: string, ...args: unknown[]): void {
        this.log('INFO', message, ...args);
    }

    public static warn(message: string, ...args: unknown[]): void {
        this.log('WARN', message, ...args);
    }

    public static error(message: string, ...args: unknown[]): void {
        this.log('ERROR', message, ...args);
    }

    private static log(level: string, message: string, ...args: unknown[]): void {
        const timestamp = new Date().toISOString();
        const formattedArgs = args.length > 0 ? ' ' + JSON.stringify(args) : '';
        const line = `[${timestamp}] [${level}] ${message}${formattedArgs}`;
        if (this.channel) {
            this.channel.appendLine(line);
        }
    }

    public static show(): void {
        if (this.channel) {
            this.channel.show();
        }
    }
}
