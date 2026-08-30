# Member 4 — Core Engine: Development Instructions

> **Owner**: Member 4
> **Language**: Python 3.11+
> **Runtime**: Local async service

---

## 1. Environment Setup

### 1.1 Prerequisites

| Tool | Version | Installation |
|:---|:---|:---|
| Python | 3.11+ (3.12 recommended) | [python.org](https://www.python.org) |
| pip | Latest | Comes with Python |
| Git | 2.40+ | [git-scm.com](https://git-scm.com) |

### 1.2 Initial Setup

```bash
cd member-4_core-engine

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment config
copy ..\env\member-4\.env.example .env
# Edit .env with your local settings
```

---

## 2. Dependencies

### 2.1 Python Packages

```
# Core
aiohttp>=3.9.0
websockets>=12.0
python-dotenv>=1.0.0

# Database
# sqlite3 is in Python stdlib — no extra install needed

# Utilities
uuid6>=2024.0.0

# Dev
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-aiohttp>=1.0.0
black>=24.0.0
ruff>=0.5.0
mypy>=1.10.0
```

---

## 3. Configuration

### 3.1 Environment Variables

Located in `../env/member-4/.env.example`:

```env
# Server
TESSERACT_CORE_HOST=localhost
TESSERACT_CORE_PORT=9700
TESSERACT_SHARED_SECRET=

# AI Layer (Member 5)
TESSERACT_AI_HOST=localhost
TESSERACT_AI_PORT=9701

# Event Processing
TESSERACT_DEDUP_WINDOW_MS=2000
TESSERACT_SESSION_IDLE_TIMEOUT_S=300
TESSERACT_EPISODE_GAP_TIMEOUT_S=1800

# Stuck Detection
TESSERACT_FRICTION_THRESHOLD_LOW=0.3
TESSERACT_FRICTION_THRESHOLD_MEDIUM=0.5
TESSERACT_FRICTION_THRESHOLD_HIGH=0.7
TESSERACT_FRICTION_DECAY_RATE=0.95

# Data Retention
TESSERACT_RAW_EVENT_RETENTION_DAYS=30
TESSERACT_STRUCTURED_EVENT_RETENTION_DAYS=90

# Database
TESSERACT_DB_PATH=~/.tesseract/data/core.db

# Logging
TESSERACT_LOG_LEVEL=DEBUG
```

---

## 4. Development Commands

```bash
# Activate venv
.venv\Scripts\activate

# Run the Core Engine
python -m core_engine

# Run with mock AI layer (no Member 5 needed)
python -m core_engine --mock-ai

# Run with debug logging
python -m core_engine --log-level=DEBUG

# Lint
ruff check .

# Format
black .

# Type check
mypy src/

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html
```

---

## 5. Testing

### 5.1 Unit Tests

```bash
pytest tests/
```

### 5.2 Mock Event Generator

During Phase 1, generate synthetic events to test the pipeline without real sensors:

```bash
# Run the built-in event generator
python -m core_engine.mock_generator
```

This should emit a realistic sequence of events simulating a user:
1. Opening VS Code
2. Writing C code
3. Running and getting errors
4. Searching Google
5. Watching YouTube
6. Retrying and succeeding

### 5.3 Testing the REST API

```bash
# Test with curl
curl http://localhost:9700/api/v1/context/current
curl http://localhost:9700/api/v1/friction/current
curl http://localhost:9700/api/v1/episodes/recent
```

### 5.4 Testing WebSocket

```bash
# Connect to the alert stream
npx wscat -c ws://localhost:9700/alerts
```

---

## 6. Debugging

### 6.1 Database Inspection

```bash
# Open the SQLite database
python -c "
import sqlite3
conn = sqlite3.connect('~/.tesseract/data/core.db')
cursor = conn.execute('SELECT COUNT(*) FROM events')
print(f'Total events: {cursor.fetchone()[0]}')
"
```

### 6.2 Logging

Use structured logging:
```python
import logging
logger = logging.getLogger("tesseract.core_engine")
logger.info("Event received", extra={"source": "browser", "type": "tab_activated"})
```

---

## 7. API Requirements

### 7.1 WebSocket Server (inbound — sensors)

| Property | Value |
|:---|:---|
| Protocol | WebSocket |
| Endpoint | `ws://localhost:9700/events` |
| Auth | Validate `Authorization: Bearer <secret>` on handshake |
| Accept | TesseractEvent JSON from any sensor |

### 7.2 REST API (outbound — UI)

| Property | Value |
|:---|:---|
| Protocol | HTTP (REST) |
| Base URL | `http://localhost:9700/api/v1` |
| Format | JSON |

### 7.3 WebSocket Server (outbound — alerts)

| Property | Value |
|:---|:---|
| Protocol | WebSocket |
| Endpoint | `ws://localhost:9700/alerts` |
| Direction | Server → Client (push alerts) |

### 7.4 REST Client (outbound — AI Layer)

| Property | Value |
|:---|:---|
| Protocol | HTTP (REST) |
| Base URL | `http://localhost:9701/api/v1` |
| Fallback | If AI Layer is unavailable, skip AI classification |

---

## 8. Model Requirements

**None.** This is a deterministic component. The Core Engine does **not** load or run any AI models. It makes HTTP requests to Member 5's API when AI reasoning is needed.

---

## 9. Git Instructions

### 9.1 Branch Naming

```
member-4/{type}-{description}
```

Examples:
- `member-4/feat-websocket-server`
- `member-4/feat-stuck-detector`
- `member-4/feat-episode-grouper`
- `member-4/fix-dedup-timing`

### 9.2 Commit Convention

```
[M4] type: short description
```

### 9.3 Folder Discipline

**You may ONLY modify files inside `member-4_core-engine/`.**

---

## 10. Integration Instructions (Phase 2+)

### With Sensors (Members 1, 2, 3)
1. Start the Core Engine: `python -m core_engine`
2. Start one or more sensors
3. Verify events appear in the Core Engine logs
4. Check the SQLite database for stored events
5. Verify deduplication by sending duplicate events

### With AI Layer (Member 5)
1. Start Member 5's AI service on port 9701
2. Start the Core Engine without `--mock-ai`
3. Trigger an ambiguous classification scenario
4. Verify the Core Engine calls Member 5's `/inference/classify` endpoint

### With UI (Member 6)
1. Start the Core Engine
2. Start Member 6's UI
3. Verify the UI can query REST endpoints
4. Trigger a stuck detection and verify the alert appears in the UI
