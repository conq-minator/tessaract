/**
 * Resilient WebSocket Client for streaming TesseractEvents to Member 4 Core Engine.
 */

import WebSocket from 'ws';
import { TesseractEvent } from '../types/events';
import { Logger } from '../utils/logger';

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'paused';

export class WebSocketClient {
    private ws: WebSocket | null = null;
    private url: string;
    private secret: string;
    private buffer: TesseractEvent[] = [];
    private maxBufferSize: number;
    private reconnectIntervalMs: number;
    private reconnectTimer: NodeJS.Timeout | null = null;
    private isPaused: boolean = false;
    private statusListeners: ((status: ConnectionStatus) => void)[] = [];

    constructor(
        url: string = 'ws://localhost:9700/events',
        secret: string = '',
        maxBufferSize: number = 100,
        reconnectIntervalMs: number = 5000
    ) {
        this.url = url;
        this.secret = secret;
        this.maxBufferSize = maxBufferSize;
        this.reconnectIntervalMs = reconnectIntervalMs;
    }

    public updateConfig(url: string, secret: string): void {
        const needsReconnect = this.url !== url || this.secret !== secret;
        this.url = url;
        this.secret = secret;
        if (needsReconnect && !this.isPaused) {
            this.disconnect();
            this.connect();
        }
    }

    public onStatusChange(listener: (status: ConnectionStatus) => void): void {
        this.statusListeners.push(listener);
    }

    private emitStatus(status: ConnectionStatus): void {
        for (const listener of this.statusListeners) {
            try {
                listener(status);
            } catch (e) {
                Logger.error('Status listener error:', e);
            }
        }
    }

    public connect(): void {
        if (this.isPaused) {
            this.emitStatus('paused');
            return;
        }

        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            return;
        }

        this.emitStatus('connecting');
        Logger.info(`Connecting to Core Engine WebSocket at ${this.url}...`);

        try {
            const headers: Record<string, string> = {};
            if (this.secret) {
                headers['Authorization'] = `Bearer ${this.secret}`;
            }

            this.ws = new WebSocket(this.url, { headers });

            this.ws.on('open', () => {
                Logger.info('WebSocket connected successfully to Core Engine.');
                this.emitStatus('connected');
                this.flushBuffer();
            });

            this.ws.on('close', (code, reason) => {
                Logger.warn(`WebSocket disconnected (code: ${code}, reason: ${reason}).`);
                this.emitStatus(this.isPaused ? 'paused' : 'disconnected');
                this.scheduleReconnect();
            });

            this.ws.on('error', (err) => {
                Logger.warn(`WebSocket connection error: ${err.message}`);
                // Error triggers close event
            });
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : String(err);
            Logger.error(`Failed to initiate WebSocket connection: ${message}`);
            this.emitStatus('disconnected');
            this.scheduleReconnect();
        }
    }

    public send(event: TesseractEvent): void {
        if (this.isPaused) return;

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify(event));
                Logger.debug(`Sent event: ${event.event_type} (${event.event_id})`);
            } catch (err: unknown) {
                const message = err instanceof Error ? err.message : String(err);
                Logger.warn(`Failed to send event immediately, buffering: ${message}`);
                this.bufferEvent(event);
            }
        } else {
            this.bufferEvent(event);
        }
    }

    private bufferEvent(event: TesseractEvent): void {
        if (this.buffer.length >= this.maxBufferSize) {
            this.buffer.shift(); // Evict oldest event (circular buffer)
        }
        this.buffer.push(event);
        Logger.debug(`Buffered event: ${event.event_type}. Buffer size: ${this.buffer.length}`);
    }

    private flushBuffer(): void {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

        while (this.buffer.length > 0) {
            const event = this.buffer.shift();
            if (event) {
                try {
                    this.ws.send(JSON.stringify(event));
                    Logger.debug(`Flushed buffered event: ${event.event_type}`);
                } catch (err: unknown) {
                    const message = err instanceof Error ? err.message : String(err);
                    Logger.warn(`Failed to flush buffered event: ${message}`);
                    this.buffer.unshift(event);
                    break;
                }
            }
        }
    }

    private scheduleReconnect(): void {
        if (this.isPaused || this.reconnectTimer) return;

        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
        }, this.reconnectIntervalMs);
    }

    public pause(): void {
        this.isPaused = true;
        this.disconnect();
        this.emitStatus('paused');
        Logger.info('Tesseract sensor paused by user.');
    }

    public resume(): void {
        this.isPaused = false;
        Logger.info('Tesseract sensor resumed by user.');
        this.connect();
    }

    public isRunning(): boolean {
        return !this.isPaused;
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
