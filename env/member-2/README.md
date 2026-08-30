# Member 2 — VS Code Sensor: Environment Setup

## Required Environment Variables

| Variable | Description | Example |
|:---|:---|:---|
| `TESSERACT_CORE_WS_URL` | WebSocket URL of the Core Engine event server | `ws://localhost:9700/events` |
| `TESSERACT_SHARED_SECRET` | Shared secret for authenticating with the Core Engine | (generate locally) |
| `TESSERACT_BUFFER_SIZE` | Max events to buffer when WebSocket is disconnected | `100` |
| `TESSERACT_RECONNECT_INTERVAL_MS` | Time between WebSocket reconnect attempts | `5000` |
| `TESSERACT_TERMINAL_CAPTURE` | Enable terminal output capture | `true` |
| `TESSERACT_EDIT_DEBOUNCE_MS` | Debounce interval for edit events | `2000` |
| `TESSERACT_LOG_LEVEL` | Logging verbosity | `DEBUG` |

## Setup

1. Copy `.env.example` to `.env` in your working directory
2. Use the same `TESSERACT_SHARED_SECRET` as all other members

## External Services

| Service | Required | Notes |
|:---|:---|:---|
| Core Engine (Member 4) | Yes (at runtime) | Must be running on port 9700 |

## API Keys

**None required.**
