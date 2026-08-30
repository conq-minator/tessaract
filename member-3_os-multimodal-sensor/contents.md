# Member 3 — OS & Multimodal Sensor

> **Owner**: Member 3
> **Folder**: `member-3_os-multimodal-sensor/`
> **Status**: Phase 0 — Documentation

---

## 1. Component Responsibility

Member 3 owns the **OS-level monitoring and multimodal input pipeline**. This includes file system watching, application usage tracking, clipboard monitoring, OCR processing, and image/document ingestion.

This is a **sensor + local processor** — it collects OS events, processes multimodal inputs (OCR, document parsing), and emits structured events to the Tesseract Core Engine. It does **not** perform behavioral analysis or AI reasoning.

---

## 2. Features

### 2.1 File System Watcher
- Monitor designated directories for file creation, modification, deletion
- Track file type, size, and modification patterns
- Detect project-related file changes (source code, documents, notes)

### 2.2 Application Usage Monitor
- Track active/foreground application name
- Detect application switches and time spent per application
- Identify which applications are relevant to learning/work context

### 2.3 Clipboard Monitor (opt-in)
- Capture text clipboard content when the user explicitly enables this
- Detect copy-paste patterns (e.g., copying error messages)
- Respect privacy — only capture when explicitly permitted

### 2.4 OCR Pipeline
- Process images and screenshots through PaddleOCR
- Extract text from handwritten notes
- Extract mathematical formulas (LaTeX output)
- Detect and classify input type (printed text, handwriting, diagram, formula)

### 2.5 Image & Document Ingestion
- Accept user-submitted images for analysis
- Parse PDF documents and extract text
- Index documents for full-text search
- Generate metadata (type, language, page count)

### 2.6 Screenshot Capture (opt-in)
- Periodic or on-demand screenshots of the active window
- Process through OCR pipeline
- Only when user has explicitly enabled this feature

### 2.7 WebSocket Event Emitter
- Emit all events to Core Engine over WebSocket
- Buffer events during disconnection

---

## 3. Internal Architecture

```
┌──────────────────────────────────────────────────────┐
│            OS & Multimodal Sensor                     │
│                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │File      │  │App Usage │  │Clipboard         │  │
│  │Watcher   │  │Monitor   │  │Monitor (opt-in)  │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       │              │                  │            │
│  ┌────┴─────┐  ┌────┴──────────────────┴──────┐    │
│  │Screenshot│  │     Image/Doc Ingestion       │    │
│  │Capture   │  │  (User-submitted or watched)  │    │
│  └────┬─────┘  └────────────┬─────────────────┘    │
│       │                     │                        │
│       ↓                     ↓                        │
│  ┌──────────────────────────────────────────────┐   │
│  │             OCR Pipeline                      │   │
│  │   (PaddleOCR — text, handwriting, formulas)   │   │
│  └──────────────────┬───────────────────────────┘   │
│                     │                                │
│                     ↓                                │
│  ┌──────────────────────────────────────────────┐   │
│  │           Event Formatter                     │   │
│  │     (Converts to TesseractEvent JSON)         │   │
│  └──────────────────┬───────────────────────────┘   │
│                     ↓                                │
│  ┌──────────────────────────────────────────────┐   │
│  │         WebSocket Client                      │   │
│  └──────────────────┬───────────────────────────┘   │
│                     ↓                                │
└─────────────────────┼────────────────────────────────┘
                      ↓
              ws://localhost:9700/events
              (Member 4 — Core Engine)
```

---

## 4. Inputs

| Input | Source | Description |
|:---|:---|:---|
| File system events | `watchdog` library | File create/modify/delete |
| Active app info | `psutil` + OS APIs | Foreground window name |
| Clipboard content | `pyperclip` | Text clipboard (opt-in) |
| Images | User submission / screenshot | Image files for OCR |
| Documents | User submission / file watcher | PDFs, text files |
| WebSocket config | `.env` | Core Engine host/port, shared secret |

---

## 5. Outputs

All outputs are **TesseractEvent** JSON messages sent over WebSocket to Member 4.

| Event Type | Payload Fields |
|:---|:---|
| `app_switched` | `from_app`, `to_app`, `duration_ms` |
| `file_created` | `file_path`, `file_type`, `size_bytes` |
| `file_modified` | `file_path`, `file_type`, `change_type` |
| `file_deleted` | `file_path`, `file_type` |
| `screenshot_captured` | `image_path`, `ocr_text`, `context` |
| `image_submitted` | `image_path`, `ocr_text`, `detected_type` |
| `document_indexed` | `file_path`, `doc_type`, `text_content`, `page_count` |
| `clipboard_text` | `text_content`, `source_app` |
| `handwriting_detected` | `image_path`, `extracted_text`, `confidence` |
| `formula_detected` | `image_path`, `latex_output`, `confidence` |
| `diagram_detected` | `image_path`, `description`, `type` |

---

## 6. APIs Used

### Python Libraries

| Library | Purpose |
|:---|:---|
| `watchdog` | File system event monitoring |
| `psutil` | Process and system monitoring |
| `PaddleOCR` | OCR for text, handwriting, formulas |
| `Pillow` (PIL) | Image processing |
| `PyMuPDF` (fitz) | PDF text extraction |
| `pyperclip` | Clipboard access |
| `websockets` | WebSocket client |

### OS-Specific APIs

| Platform | API | Purpose |
|:---|:---|:---|
| Windows | `ctypes` + `win32gui` | Active window detection |
| Linux | `xdotool` / `xprop` | Active window detection |
| macOS | `AppKit` via `pyobjc` | Active window detection |

---

## 7. Data Structures

### TesseractEvent (output format)

```json
{
  "event_id": "uuid-v4",
  "source": "os",
  "event_type": "image_submitted",
  "timestamp": "2026-08-30T10:15:30.000Z",
  "payload": {
    "image_path": "/home/user/notes/math_homework.jpg",
    "ocr_text": "∫ x² dx = x³/3 + C",
    "detected_type": "formula"
  },
  "metadata": {
    "session_id": "uuid-v4",
    "confidence": 0.87,
    "privacy_level": "local_only"
  }
}
```

---

## 8. Dependencies

### Internal Dependencies (at runtime)

| Dependency | Member | Interface |
|:---|:---|:---|
| Core Engine WebSocket server | Member 4 | `ws://localhost:9700/events` |

### External Dependencies

| Package | Purpose | Size Impact |
|:---|:---|:---|
| `PaddleOCR` | OCR engine | ~500 MB (includes models) |
| `watchdog` | File system monitoring | Minimal |
| `psutil` | System/process info | Minimal |
| `websockets` | WebSocket client | Minimal |
| `Pillow` | Image processing | ~30 MB |
| `PyMuPDF` | PDF extraction | ~20 MB |

---

## 9. Interfaces

### 9.1 Outbound: Sensor → Core Engine

- **Interface Name**: `SensorEventStream`
- **Owner**: Member 4 (server)
- **Consumer**: Member 3 (client)
- **Protocol**: WebSocket
- **Endpoint**: `ws://localhost:9700/events`
- **Data Format**: JSON (TesseractEvent)
- **Auth**: `Authorization: Bearer <TESSERACT_SHARED_SECRET>` header on WS handshake

---

## 10. Testing

### Unit Tests
- File watcher correctly emits create/modify/delete events
- App usage monitor detects application switches
- OCR pipeline correctly extracts text from test images
- Formula detector outputs valid LaTeX
- Handwriting detector produces readable text
- Event formatter produces valid TesseractEvent JSON

### Integration Tests (Phase 2+)
- Events arrive at Core Engine with correct schema
- OCR results are accurate for test images
- File watcher handles rapid file changes without flooding

---

## 11. Definition of Done

- [ ] File system watcher detects create/modify/delete in watched directories
- [ ] Application usage monitor tracks active app and switch events
- [ ] OCR pipeline processes images and extracts text accurately
- [ ] Handwriting and formula detection produces usable output
- [ ] PDF documents are parsed and text is extracted
- [ ] All events conform to TesseractEvent schema
- [ ] WebSocket connection to Core Engine works reliably
- [ ] Platform abstraction works on Windows (minimum)
- [ ] OCR models load lazily (not on startup)
- [ ] All unit tests pass

---

## 12. What This Member Owns

- File system watcher
- Application usage monitor
- Clipboard monitor
- Screenshot capture
- OCR pipeline (PaddleOCR integration)
- Image/document ingestion and parsing
- Handwriting/formula/diagram detection
- PDF text extraction
- WebSocket client (OS sensor side)
- Platform abstraction layer for OS APIs

---

## 13. What This Member Does NOT Own

- Event analysis or interpretation (Member 4)
- WebSocket server (Member 4)
- AI inference / language models (Member 5)
- Knowledge graph (Member 5)
- User interface / notifications (Member 6)
- Browser sensor (Member 1)
- VS Code sensor (Member 2)
- VLM-based image understanding (Member 5 — this member only does OCR)
