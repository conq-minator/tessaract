# Member 1 — Browser Sensor: Environment Setup

## Required Environment Variables

| Variable | Description | Example |
|:---|:---|:---|
| `TESSERACT_CORE_WS_URL` | WebSocket URL of the Core Engine event server | `ws://localhost:9700/events` |
| `TESSERACT_SHARED_SECRET` | Shared secret for authenticating with the Core Engine | (generate locally) |
| `TESSERACT_BUFFER_SIZE` | Max events to buffer when WebSocket is disconnected | `100` |
| `TESSERACT_RECONNECT_INTERVAL_MS` | Time between WebSocket reconnect attempts | `5000` |
| `TESSERACT_LOG_LEVEL` | Logging verbosity | `DEBUG`, `INFO`, `WARN`, `ERROR` |

## Setup

1. Copy `.env.example` to `.env` in your working directory
2. Generate a shared secret (must match all other members):
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
3. Set `TESSERACT_SHARED_SECRET` to the generated value

## External Services

| Service | Required | Notes |
|:---|:---|:---|
| Core Engine (Member 4) | Yes (at runtime) | Must be running on port 9700 for events to be received |

## API Keys

**None required.** The browser sensor does not call any external APIs.
