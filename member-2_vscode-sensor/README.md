# Tesseract VS Code Sensor

Developer activity sensor for Tesseract Behavioral AI Copilot.

## Features

- **Editor Activity Tracking**: Tracks file open/close/save and debounced editing activity.
- **Compiler & Diagnostic Detection**: Observes errors and warnings, capturing error messages and line numbers.
- **Terminal Execution Capture**: Tracks terminal command executions and exit codes.
- **Debug Session Tracking**: Observes debug sessions and breakpoints.
- **Privacy-First**: Automatically redacts passwords, tokens, API keys, and sensitive paths.
- **Resilient Transport**: Streams structured JSON events to Tesseract Core Engine over WebSocket (`ws://localhost:9700/events`) with local buffering and automatic reconnection.

## Extension Settings

This extension contributes the following settings:

* `tesseract.coreWsUrl`: WebSocket endpoint of the Tesseract Core Engine (`ws://localhost:9700/events`).
* `tesseract.sharedSecret`: Shared authentication secret for Core Engine WebSocket handshake.
* `tesseract.bufferSize`: Maximum number of events to buffer locally when offline.
* `tesseract.reconnectIntervalMs`: Reconnection retry interval in milliseconds.
* `tesseract.editDebounceMs`: Debounce duration for high-frequency editor events.

## Commands

- `Tesseract: Toggle Sensor`: Pause or resume sensor tracking.
- `Tesseract: Show Sensor Health & Metrics`: Display current connection status and session metrics.
