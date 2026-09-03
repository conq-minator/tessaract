/**
 * Configuration interfaces for Tesseract VS Code Sensor.
 */

export interface SensorConfig {
    coreWsUrl: string;
    sharedSecret: string;
    bufferSize: number;
    reconnectIntervalMs: number;
    terminalCapture: boolean;
    editDebounceMs: number;
    pathRedaction: 'relative' | 'full' | 'anonymized';
    logLevel: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
}
