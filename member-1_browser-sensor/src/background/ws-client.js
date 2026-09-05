/**
 * Resilient WebSocket Client for Tesseract Browser Sensor
 * Manages persistent connection to Core Engine (ws://localhost:9700/events),
 * in-memory buffering (max 100 events), and exponential backoff reconnection.
 */

class TesseractWSClient {
    constructor(url = 'ws://localhost:9700/events', maxBufferSize = 100) {
        this.url = url;
        this.maxBufferSize = maxBufferSize;
        this.ws = null;
        this.buffer = [];
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.reconnectTimer = null;
        this.statusListeners = [];
        this.totalSentCount = 0;
        this.lastEvents = [];
    }

    connect() {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            return;
        }

        try {
            console.log(`[TesseractSensor] Connecting to ${this.url}...`);
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                console.log('[TesseractSensor] WebSocket connection established.');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this._notifyStatus('connected');
                this._flushBuffer();
            };

            this.ws.onmessage = (msg) => {
                try {
                    const data = JSON.parse(msg.data);
                    console.log('[TesseractSensor] Server message:', data);
                } catch (e) {}
            };

            this.ws.onerror = (err) => {
                console.warn('[TesseractSensor] WebSocket error:', err);
            };

            this.ws.onclose = (ev) => {
                console.log(`[TesseractSensor] WebSocket closed (code: ${ev.code}). Scheduling reconnect...`);
                this.isConnected = false;
                this._notifyStatus('disconnected');
                this._scheduleReconnect();
            };
        } catch (e) {
            console.error('[TesseractSensor] WebSocket initialization failed:', e);
            this.isConnected = false;
            this._scheduleReconnect();
        }
    }

    sendEvent(event) {
        // Keep in local last events list for popup
        this.lastEvents.unshift(event);
        if (this.lastEvents.length > 10) {
            this.lastEvents.pop();
        }

        if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify(event));
                this.totalSentCount++;
                return true;
            } catch (err) {
                console.warn('[TesseractSensor] Send failed, buffering event:', err);
                this._bufferEvent(event);
                return false;
            }
        } else {
            this._bufferEvent(event);
            return false;
        }
    }

    _bufferEvent(event) {
        if (this.buffer.length >= this.maxBufferSize) {
            this.buffer.shift(); // Drop oldest event if buffer is full
        }
        this.buffer.push(event);
        console.log(`[TesseractSensor] Buffered event (${this.buffer.length}/${this.maxBufferSize})`);
    }

    _flushBuffer() {
        if (this.buffer.length === 0) return;
        console.log(`[TesseractSensor] Flushing ${this.buffer.length} buffered events...`);
        while (this.buffer.length > 0 && this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
            const ev = this.buffer.shift();
            try {
                this.ws.send(JSON.stringify(ev));
                this.totalSentCount++;
            } catch (err) {
                console.error('[TesseractSensor] Error flushing event, re-buffering:', err);
                this.buffer.unshift(ev);
                break;
            }
        }
    }

    _scheduleReconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }
        this.reconnectAttempts++;
        // Exponential backoff: 1s, 2s, 4s, 8s, max 10s
        const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts - 1), 10000);
        console.log(`[TesseractSensor] Reconnecting in ${Math.round(delay)}ms (attempt ${this.reconnectAttempts})...`);
        this._notifyStatus('reconnecting');
        this.reconnectTimer = setTimeout(() => {
            this.connect();
        }, delay);
    }

    onStatusChange(callback) {
        this.statusListeners.push(callback);
    }

    _notifyStatus(status) {
        this.statusListeners.forEach(fn => {
            try { fn(status); } catch (e) {}
        });
    }

    getStatus() {
        return {
            connected: this.isConnected,
            bufferedCount: this.buffer.length,
            totalSent: this.totalSentCount,
            recentEvents: this.lastEvents.slice(0, 5)
        };
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TesseractWSClient };
}
