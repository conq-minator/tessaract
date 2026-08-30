# Member 3 — OS & Multimodal Sensor: Development Instructions

> **Owner**: Member 3
> **Language**: Python 3.11+
> **Runtime**: Local system service

---

## 1. Environment Setup

### 1.1 Prerequisites

| Tool | Version | Installation |
|:---|:---|:---|
| Python | 3.11+ (3.12 recommended) | [python.org](https://www.python.org) |
| pip | Latest | Comes with Python |
| Git | 2.40+ | [git-scm.com](https://git-scm.com) |
| MSVC Build Tools | 2022+ (Windows, only if building PaddleOCR from source) | [Visual Studio](https://visualstudio.microsoft.com/downloads/) |

### 1.2 Initial Setup

```bash
cd member-3_os-multimodal-sensor

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/macOS)
# source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment config
copy ..\env\member-3\.env.example .env
# Edit .env with your local settings
```

---

## 2. Dependencies

### 2.1 Python Packages

```
# Core
watchdog>=4.0.0
psutil>=6.0.0
websockets>=12.0
Pillow>=10.0.0
PyMuPDF>=1.24.0
pyperclip>=1.9.0

# OCR
paddlepaddle>=2.6.0
paddleocr>=2.8.0

# Utilities
python-dotenv>=1.0.0
uuid6>=2024.0.0

# Dev
pytest>=8.0.0
pytest-asyncio>=0.23.0
black>=24.0.0
ruff>=0.5.0
mypy>=1.10.0
```

### 2.2 PaddleOCR Installation Notes

PaddleOCR has large model files (~500 MB total). Models are downloaded on first use.

```bash
# Install PaddlePaddle (CPU version — sufficient for OCR)
pip install paddlepaddle

# Install PaddleOCR
pip install paddleocr
```

On Windows, if PaddlePaddle fails to install via pip, use the official wheel:
```bash
pip install paddlepaddle -f https://www.paddlepaddle.org.cn/whl/windows/cpu-mkl-avx/stable.html
```

### 2.3 Platform-Specific Dependencies

| Platform | Extra Package | Purpose |
|:---|:---|:---|
| Windows | `pywin32` | Active window detection via Win32 API |
| Linux | (none, uses `xdotool` CLI) | Active window detection |
| macOS | `pyobjc-framework-AppKit` | Active window detection |

---

## 3. Configuration

### 3.1 Environment Variables

Located in `../env/member-3/.env.example`:

```env
TESSERACT_CORE_WS_URL=ws://localhost:9700/events
TESSERACT_SHARED_SECRET=

# File Watcher
TESSERACT_WATCH_DIRS=~/Documents,~/Projects,~/Desktop
TESSERACT_WATCH_EXTENSIONS=.py,.c,.cpp,.js,.ts,.md,.txt,.pdf,.docx
TESSERACT_IGNORE_DIRS=.git,node_modules,__pycache__,.venv

# App Monitor
TESSERACT_APP_POLL_INTERVAL_S=5
TESSERACT_APP_IDLE_TIMEOUT_S=300

# OCR
TESSERACT_OCR_LANG=en
TESSERACT_OCR_ENABLE_FORMULA=true
TESSERACT_OCR_ENABLE_HANDWRITING=true
TESSERACT_OCR_LAZY_LOAD=true

# Clipboard (opt-in)
TESSERACT_CLIPBOARD_ENABLED=false

# Screenshot (opt-in)
TESSERACT_SCREENSHOT_ENABLED=false
TESSERACT_SCREENSHOT_INTERVAL_S=60

# Privacy
TESSERACT_MAX_FILE_CONTENT_BYTES=10240
```

---

## 4. Development Commands

```bash
# Activate venv
.venv\Scripts\activate

# Run the sensor
python -m os_sensor

# Run with debug logging
python -m os_sensor --log-level=DEBUG

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

Provide test images in `tests/fixtures/`:
- `printed_text.png` — clear printed text
- `handwritten_note.jpg` — handwritten text sample
- `math_formula.png` — mathematical formula
- `diagram.png` — technical diagram
- `screenshot.png` — application screenshot

### 5.2 Mock WebSocket Server

During Phase 1:
```bash
# Simple WebSocket echo server
python -c "
import asyncio, websockets
async def echo(ws):
    async for msg in ws:
        print(msg)
asyncio.run(websockets.serve(echo, 'localhost', 9700))
"
```

---

## 6. Debugging

### 6.1 Common Issues

| Issue | Solution |
|:---|:---|
| PaddleOCR fails to import | Ensure PaddlePaddle is installed first |
| `pywin32` import error | Run `python Scripts/pywin32_postinstall.py -install` |
| File watcher misses events | Check `TESSERACT_WATCH_DIRS` paths exist |
| High CPU from file watcher | Add noisy directories to `TESSERACT_IGNORE_DIRS` |
| OCR slow on first run | Models download on first use (~500 MB) |

### 6.2 Logging

Use Python's `logging` module:
```python
import logging
logger = logging.getLogger("tesseract.os_sensor")
logger.info("File modified: %s", file_path)
```

---

## 7. API Requirements

### 7.1 Outbound WebSocket

| Property | Value |
|:---|:---|
| Protocol | WebSocket |
| Endpoint | `ws://localhost:9700/events` |
| Auth | `Authorization: Bearer <secret>` on handshake |
| Payload | TesseractEvent JSON |
| Reconnect | Auto-reconnect with exponential backoff |
| Buffer | Queue events when disconnected (max configurable) |

---

## 8. Model Requirements

| Model | Purpose | Size | Loaded |
|:---|:---|:---|:---|
| PaddleOCR detection model | Text region detection | ~5 MB | Lazy (on first OCR call) |
| PaddleOCR recognition model | Text recognition | ~10 MB | Lazy |
| PaddleOCR formula model | Mathematical formula recognition | ~15 MB | Lazy (if enabled) |

These are **not** LLMs. They are lightweight, specialized models bundled with PaddleOCR. They run on CPU efficiently.

Member 3 does NOT load or use LLMs. If VLM-based interpretation is needed (e.g., understanding a diagram), the event is sent to Member 5 via Member 4.

---

## 9. Git Instructions

### 9.1 Branch Naming

```
member-3/{type}-{description}
```

Examples:
- `member-3/feat-file-watcher`
- `member-3/feat-ocr-pipeline`
- `member-3/fix-app-monitor-windows`

### 9.2 Commit Convention

```
[M3] type: short description
```

### 9.3 Folder Discipline

**You may ONLY modify files inside `member-3_os-multimodal-sensor/`.**

---

## 10. Integration Instructions (Phase 2+)

1. Ensure Member 4's Core Engine is running on port 9700
2. Start the OS sensor: `python -m os_sensor`
3. Create/modify/delete files in watched directories
4. Switch between applications
5. Submit a test image for OCR
6. Verify all events appear in Core Engine logs with correct schemas
