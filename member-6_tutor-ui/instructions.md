# Member 6 — Tutor & UI: Development Instructions

> **Owner**: Member 6
> **Language**: Python 3.11+ (backend) + HTML/CSS/JS (frontend)
> **Runtime**: Local web server + system tray app

---

## 1. Environment Setup

### 1.1 Prerequisites

| Tool | Version | Installation |
|:---|:---|:---|
| Python | 3.11+ (3.12 recommended) | [python.org](https://www.python.org) |
| pip | Latest | Comes with Python |
| Node.js | 20 LTS+ (for frontend build tools, if needed) | [nodejs.org](https://nodejs.org) |
| Git | 2.40+ | [git-scm.com](https://git-scm.com) |

### 1.2 Initial Setup

```bash
cd member-6_tutor-ui

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment config
copy ..\env\member-6\.env.example .env
# Edit .env with your local settings
```

---

## 2. Dependencies

### 2.1 Python Packages

```
# Backend
aiohttp>=3.9.0
httpx>=0.27.0
websockets>=12.0
jinja2>=3.1.0
python-dotenv>=1.0.0

# System Tray
pystray>=0.19.0
Pillow>=10.0.0

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

### 2.2 Frontend Libraries (loaded via CDN or bundled)

| Library | Purpose | Loaded |
|:---|:---|:---|
| D3.js or vis.js | Knowledge graph visualization | CDN |
| Chart.js | Analytics charts | CDN |
| (No framework) | Vanilla JS for interactivity | — |

The frontend is intentionally lightweight — no React, Vue, or heavy framework. Pure HTML/CSS/JS with a few visualization libraries.

---

## 3. Configuration

### 3.1 Environment Variables

Located in `../env/member-6/.env.example`:

```env
# Server
TESSERACT_UI_HOST=localhost
TESSERACT_UI_PORT=9702

# Upstream Services
TESSERACT_CORE_HOST=localhost
TESSERACT_CORE_PORT=9700
TESSERACT_AI_HOST=localhost
TESSERACT_AI_PORT=9701
TESSERACT_SHARED_SECRET=

# UI Settings
TESSERACT_NOTIFICATION_COOLDOWN_S=300
TESSERACT_DEFAULT_AUTONOMY_LEVEL=2
TESSERACT_THEME=dark

# Logging
TESSERACT_LOG_LEVEL=DEBUG
```

---

## 4. Development Commands

```bash
# Activate venv
.venv\Scripts\activate

# Run the Tutor/UI service (dashboard + system tray)
python -m tutor_ui

# Run dashboard only (no system tray — useful for development)
python -m tutor_ui --no-tray

# Run with mock data (no Members 4, 5 needed)
python -m tutor_ui --mock-data

# Lint
ruff check .

# Format
black .

# Type check
mypy src/

# Run tests
pytest
```

---

## 5. Testing

### 5.1 Unit Tests

```bash
pytest tests/
```

### 5.2 Manual Testing

1. Run `python -m tutor_ui --mock-data`
2. Open `http://localhost:9702` in a browser
3. Navigate through all dashboard pages
4. Trigger mock notifications
5. Test settings page

### 5.3 Mock Data Mode

In mock mode, the service generates synthetic data for:
- Current context (learning C programming)
- Knowledge graph (sample skill tree)
- Episodes (debugging sessions with friction)
- Friction scores (varying levels)
- Notifications (stuck detection, milestones)

This allows full UI development without Members 4 or 5.

---

## 6. Debugging

### 6.1 Dashboard Debugging

- Open browser DevTools (`F12`) on `http://localhost:9702`
- Check Console for JavaScript errors
- Check Network tab for API call failures

### 6.2 System Tray Debugging

- System tray requires a desktop environment
- On headless/remote development: use `--no-tray` flag
- Check Python logs for tray-related errors

### 6.3 Logging

```python
import logging
logger = logging.getLogger("tesseract.tutor_ui")
logger.info("Hint generated", extra={"topic": "c-pointers", "level": 2})
```

---

## 7. API Requirements

### 7.1 Consumed: Core Engine (Member 4)

| Method | URL | Purpose |
|:---|:---|:---|
| GET | `http://localhost:9700/api/v1/context/current` | Current user context |
| GET | `http://localhost:9700/api/v1/friction/current` | Friction score |
| GET | `http://localhost:9700/api/v1/episodes/recent` | Recent episodes |
| GET | `http://localhost:9700/api/v1/sessions/active` | Active session |
| GET | `http://localhost:9700/api/v1/analytics/summary` | Analytics data |
| WS | `ws://localhost:9700/alerts` | Real-time alerts |

### 7.2 Consumed: AI & Knowledge (Member 5)

| Method | URL | Purpose |
|:---|:---|:---|
| GET | `http://localhost:9701/api/v1/knowledge/graph` | Knowledge graph |
| GET | `http://localhost:9701/api/v1/knowledge/gaps` | Knowledge gaps |
| POST | `http://localhost:9701/api/v1/tutor/hint` | Generate hint |
| POST | `http://localhost:9701/api/v1/tutor/explain` | Generate explanation |
| POST | `http://localhost:9701/api/v1/tutor/practice` | Generate practice |
| POST | `http://localhost:9701/api/v1/tutor/roadmap` | Generate roadmap |
| POST | `http://localhost:9701/api/v1/tutor/recommend` | Get recommendations |

---

## 8. Model Requirements

**None.** This component does not load or run AI models. All AI is accessed through Member 5's REST API.

---

## 9. Git Instructions

### 9.1 Branch Naming

```
member-6/{type}-{description}
```

Examples:
- `member-6/feat-dashboard-overview`
- `member-6/feat-kg-visualization`
- `member-6/feat-notification-system`
- `member-6/feat-system-tray`

### 9.2 Commit Convention

```
[M6] type: short description
```

### 9.3 Folder Discipline

**You may ONLY modify files inside `member-6_tutor-ui/`.**

---

## 10. Integration Instructions (Phase 2+)

### With Core Engine (Member 4)
1. Start Member 4's Core Engine on port 9700
2. Start this service (without `--mock-data`)
3. Verify the Overview page shows real context data
4. Trigger stuck detection and verify the notification appears
5. Verify episodes and sessions display correctly

### With AI & Knowledge (Member 5)
1. Start Member 5's AI service on port 9701
2. Verify the Knowledge Graph page renders real skill nodes
3. Request a hint from the dashboard and verify the response
4. Generate a roadmap and verify it displays correctly

### Full Integration
1. Start all services (Members 4, 5, 6)
2. Start sensors (Members 1, 2, 3)
3. Use the browser and VS Code normally
4. Watch the dashboard update in real time
5. Trigger a stuck scenario and verify end-to-end assistance
