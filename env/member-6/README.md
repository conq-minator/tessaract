# Member 6 — Tutor & UI: Environment Setup

## Required Environment Variables

| Variable | Description | Example |
|:---|:---|:---|
| `TESSERACT_UI_HOST` | Host to bind the dashboard server | `localhost` |
| `TESSERACT_UI_PORT` | Port for the web dashboard | `9702` |
| `TESSERACT_CORE_HOST` | Core Engine host | `localhost` |
| `TESSERACT_CORE_PORT` | Core Engine port | `9700` |
| `TESSERACT_AI_HOST` | AI & Knowledge service host | `localhost` |
| `TESSERACT_AI_PORT` | AI & Knowledge service port | `9701` |
| `TESSERACT_SHARED_SECRET` | Shared authentication secret | (generate locally) |

## UI Configuration

| Variable | Description | Default |
|:---|:---|:---|
| `TESSERACT_NOTIFICATION_COOLDOWN_S` | Min seconds between notifications | `300` (5 min) |
| `TESSERACT_DEFAULT_AUTONOMY_LEVEL` | Default autonomy level (0–5) | `2` (Suggest) |
| `TESSERACT_THEME` | Dashboard color theme | `dark` |

## Setup

1. Copy `.env.example` to `.env`
2. Use the same `TESSERACT_SHARED_SECRET` as other members
3. Ensure Members 4 and 5 are configured on their respective ports

## External Services

| Service | Required | Notes |
|:---|:---|:---|
| Core Engine (Member 4) | Yes (at runtime) | Data source for dashboard |
| AI & Knowledge (Member 5) | Yes (at runtime) | Hint/roadmap generation |

## API Keys

**None required.** All AI calls go through Member 5's API.
