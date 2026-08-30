# Member 4 — Core Engine: Environment Setup

## Required Environment Variables

| Variable | Description | Example |
|:---|:---|:---|
| `TESSERACT_CORE_HOST` | Host to bind the Core Engine server | `localhost` |
| `TESSERACT_CORE_PORT` | Port for WebSocket + REST server | `9700` |
| `TESSERACT_SHARED_SECRET` | Shared authentication secret | (generate locally) |
| `TESSERACT_AI_HOST` | Host of the AI & Knowledge service (Member 5) | `localhost` |
| `TESSERACT_AI_PORT` | Port of the AI & Knowledge service | `9701` |
| `TESSERACT_DB_PATH` | Path to the SQLite event database | `~/.tesseract/data/core.db` |

## Tunable Parameters

| Variable | Description | Default |
|:---|:---|:---|
| `TESSERACT_DEDUP_WINDOW_MS` | Time window for event deduplication | `2000` |
| `TESSERACT_SESSION_IDLE_TIMEOUT_S` | Idle time before session ends | `300` (5 min) |
| `TESSERACT_EPISODE_GAP_TIMEOUT_S` | Max gap between events in one episode | `1800` (30 min) |
| `TESSERACT_FRICTION_THRESHOLD_LOW` | Low friction threshold | `0.3` |
| `TESSERACT_FRICTION_THRESHOLD_MEDIUM` | Medium friction threshold | `0.5` |
| `TESSERACT_FRICTION_THRESHOLD_HIGH` | High friction threshold | `0.7` |
| `TESSERACT_FRICTION_DECAY_RATE` | Friction score decay per minute | `0.95` |

## Setup

1. Copy `.env.example` to `.env`
2. Generate the shared secret and distribute to all members
3. Ensure `TESSERACT_DB_PATH` directory exists (or will be auto-created)

## External Services

| Service | Required | Notes |
|:---|:---|:---|
| AI & Knowledge (Member 5) | Optional | Core Engine works without it (skips AI classification) |

## API Keys

**None required.**
