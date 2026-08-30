# Member 3 — OS & Multimodal Sensor: Environment Setup

## Required Environment Variables

| Variable | Description | Example |
|:---|:---|:---|
| `TESSERACT_CORE_WS_URL` | WebSocket URL of the Core Engine | `ws://localhost:9700/events` |
| `TESSERACT_SHARED_SECRET` | Shared authentication secret | (generate locally) |
| `TESSERACT_WATCH_DIRS` | Comma-separated directories to watch | `~/Documents,~/Projects` |
| `TESSERACT_WATCH_EXTENSIONS` | File extensions to track | `.py,.c,.cpp,.js,.md` |
| `TESSERACT_IGNORE_DIRS` | Directories to ignore | `.git,node_modules` |
| `TESSERACT_OCR_LANG` | OCR language | `en` |
| `TESSERACT_OCR_LAZY_LOAD` | Load OCR models on first use | `true` |

## Setup

1. Copy `.env.example` to `.env`
2. Adjust `TESSERACT_WATCH_DIRS` to your project directories
3. Use the same `TESSERACT_SHARED_SECRET` as other members

## External Services

| Service | Required | Notes |
|:---|:---|:---|
| Core Engine (Member 4) | Yes (at runtime) | Must be running on port 9700 |

## API Keys

**None required.** OCR uses local PaddleOCR models (downloaded on first use).

## Large Downloads

| Resource | Size | When Downloaded |
|:---|:---|:---|
| PaddleOCR models | ~500 MB | On first OCR call (lazy) |
| PaddlePaddle (CPU) | ~200 MB | During `pip install` |
