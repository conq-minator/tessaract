# Member 2 — VS Code Sensor

> **Owner**: Member 2
> **Folder**: `member-2_vscode-sensor/`
> **Status**: Phase 0 — Documentation

---

## 1. Component Responsibility

Member 2 owns the **VS Code Extension** that observes developer activity within Visual Studio Code and emits structured events to the Tesseract Core Engine.

This is a **sensor** — it collects and emits events. It does **not** analyze, classify, or interpret events. All intelligence is downstream (Members 4–6).

---

## 2. Features

### 2.1 Editor Activity Tracking
- Detect file opens, closes, and active editor switches
- Track file save events with language and change magnitude
- Monitor cursor position and selection changes (sampled, not continuous)

### 2.2 Code Execution Detection
- Detect when code is run via terminal, debug launch, or task
- Capture the language, file path, and command used

### 2.3 Error & Diagnostic Detection
- Monitor VS Code's diagnostics API for errors and warnings
- Capture error messages, file path, line number, severity
- Detect when errors appear, persist, or are resolved

### 2.4 Terminal Activity Capture
- Detect terminal creation and disposal
- Capture commands executed in the terminal
- Capture terminal output (error-focused, sampled)
- Track command exit codes and duration

### 2.5 Debug Session Tracking
- Detect debug session start, stop, pause
- Track breakpoint hits and step-through activity

### 2.6 Workspace Context
- Detect active workspace/folder
- Track workspace language composition
- Monitor extension activations (relevant to learning context)

### 2.7 WebSocket Event Emitter
- Establish persistent WebSocket connection to Core Engine (`ws://localhost:9700/events`)
- Emit all events as JSON conforming to the TesseractEvent schema
- Handle connection loss, reconnection, and event buffering

---

## 3. Internal Architecture

```
┌─────────────────────────────────────────────────┐
│            VS Code Extension                     │
│                                                  │
│  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │Editor      │  │Terminal    │  │Diagnostic │ │
│  │Tracker     │  │Monitor     │  │Watcher    │ │
│  └─────┬──────┘  └─────┬──────┘  └─────┬─────┘ │
│        │               │               │        │
│  ┌─────┴──────┐  ┌─────┴──────┐        │        │
│  │Debug       │  │Workspace   │        │        │
│  │Tracker     │  │Context     │        │        │
│  └─────┬──────┘  └─────┬──────┘        │        │
│        │               │               │        │
│        ↓               ↓               ↓        │
│  ┌──────────────────────────────────────────┐   │
│  │           Event Formatter                │   │
│  │     (Converts to TesseractEvent JSON)    │   │
│  └──────────────────┬───────────────────────┘   │
│                     ↓                            │
│  ┌──────────────────────────────────────────┐   │
│  │         WebSocket Client                 │   │
│  │     (Buffers, sends, reconnects)         │   │
│  └──────────────────┬───────────────────────┘   │
│                     ↓                            │
└─────────────────────┼────────────────────────────┘
                      ↓
              ws://localhost:9700/events
              (Member 4 — Core Engine)
```

---

## 4. Inputs

| Input | Source | Description |
|:---|:---|:---|
| Editor events | `vscode.window` API | `onDidChangeActiveTextEditor`, `onDidChangeTextEditorSelection` |
| Document events | `vscode.workspace` API | `onDidChangeTextDocument`, `onDidSaveTextDocument`, `onDidOpenTextDocument`, `onDidCloseTextDocument` |
| Diagnostic events | `vscode.languages` API | `onDidChangeDiagnostics` |
| Terminal events | `vscode.window` API | `onDidOpenTerminal`, `onDidCloseTerminal`, `onDidWriteTerminalData` (if available) |
| Debug events | `vscode.debug` API | `onDidStartDebugSession`, `onDidTerminateDebugSession`, `onDidChangeBreakpoints` |
| Task events | `vscode.tasks` API | `onDidStartTask`, `onDidEndTask` |
| WebSocket config | `.env` | Core Engine host/port, shared secret |

---

## 5. Outputs

All outputs are **TesseractEvent** JSON messages sent over WebSocket to Member 4.

| Event Type | Payload Fields |
|:---|:---|
| `file_opened` | `file_path`, `language`, `workspace` |
| `file_saved` | `file_path`, `language`, `change_size` |
| `file_closed` | `file_path`, `language`, `duration_ms` |
| `code_executed` | `file_path`, `language`, `command` |
| `error_detected` | `file_path`, `language`, `error_message`, `error_line`, `severity` |
| `error_resolved` | `file_path`, `language`, `error_message`, `error_line` |
| `terminal_command` | `command`, `exit_code`, `duration_ms` |
| `terminal_output` | `output_snippet`, `is_error` |
| `debug_started` | `file_path`, `language` |
| `debug_ended` | `file_path`, `language`, `duration_ms` |
| `debug_breakpoint_hit` | `file_path`, `line` |
| `workspace_changed` | `workspace_name`, `languages` |

---

## 6. APIs Used

### VS Code Extension APIs

| API | Purpose |
|:---|:---|
| `vscode.window.onDidChangeActiveTextEditor` | Track active file |
| `vscode.workspace.onDidSaveTextDocument` | Track saves |
| `vscode.workspace.onDidChangeTextDocument` | Track edits |
| `vscode.languages.onDidChangeDiagnostics` | Track errors/warnings |
| `vscode.window.onDidOpenTerminal` | Track terminal creation |
| `vscode.window.onDidWriteTerminalData` | Capture terminal output |
| `vscode.debug.onDidStartDebugSession` | Track debug sessions |
| `vscode.tasks.onDidEndTask` | Track task execution |

### External Communication

| Protocol | Endpoint | Direction |
|:---|:---|:---|
| WebSocket | `ws://localhost:9700/events` | Extension → Core Engine |

---

## 7. Data Structures

### TesseractEvent (output format)

```json
{
  "event_id": "uuid-v4",
  "source": "vscode",
  "event_type": "error_detected",
  "timestamp": "2026-08-30T10:15:30.000Z",
  "payload": {
    "file_path": "main.c",
    "language": "c",
    "error_message": "expected ';' before '}' token",
    "error_line": 42,
    "severity": "error"
  },
  "metadata": {
    "session_id": "uuid-v4",
    "confidence": 1.0,
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

| Package | Purpose |
|:---|:---|
| `@types/vscode` | VS Code API type definitions |
| `ws` | WebSocket client for Node.js |
| `uuid` | Event ID generation |
| `typescript` | Language (compile to JS) |

---

## 9. Interfaces

### 9.1 Outbound: Sensor → Core Engine

- **Interface Name**: `SensorEventStream`
- **Owner**: Member 4 (server)
- **Consumer**: Member 2 (client)
- **Protocol**: WebSocket
- **Endpoint**: `ws://localhost:9700/events`
- **Data Format**: JSON (TesseractEvent)
- **Auth**: `Authorization: Bearer <TESSERACT_SHARED_SECRET>` header on WS handshake

---

## 10. Testing

### Unit Tests
- Editor tracker correctly emits events for file open/close/save
- Diagnostic watcher correctly extracts error details
- Terminal monitor captures command and exit code
- Event formatter produces valid TesseractEvent JSON
- WebSocket client buffers and reconnects properly

### Integration Tests (Phase 2+)
- Extension connects to Member 4 WebSocket server
- Events arrive at Core Engine with correct schema
- Rapid editing does not flood the event stream (rate limiting works)

---

## 11. Definition of Done

- [ ] VS Code extension activates without errors
- [ ] All event types listed above are captured and emitted
- [ ] Events conform to TesseractEvent schema
- [ ] WebSocket connection to Core Engine works reliably
- [ ] Events buffer during disconnection and flush on reconnect
- [ ] Error detection captures diagnostic severity and location
- [ ] Terminal commands and exit codes are tracked
- [ ] Rate limiting prevents event flooding during rapid editing
- [ ] All unit tests pass
- [ ] Extension can be launched via F5 in Extension Development Host

---

## 12. What This Member Owns

- VS Code extension (all source code)
- Editor event capture logic
- Terminal monitoring logic
- Diagnostic/error watcher
- Debug session tracking
- WebSocket client (VS Code side)
- Extension manifest and activation
- Extension packaging (`.vsix`)

---

## 13. What This Member Does NOT Own

- Event analysis or interpretation (Member 4)
- WebSocket server (Member 4)
- Intent classification (Member 4)
- AI inference (Member 5)
- Knowledge graph (Member 5)
- User interface / notifications (Member 6)
- Browser sensor (Member 1)
- OS/file sensor (Member 3)
