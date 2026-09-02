# Member 2 — VS Code Sensor: Product Requirements Document (PRD)

> **Owner**: Member 2  
> **Last Updated**: 2026-08-31  
> **Status**: Phase 0 → Phase 1 Transition  

---

## 1. Product Purpose & Philosophy

The **VS Code Sensor** is a reliable, privacy-first behavioral activity sensor for the Tesseract Personal Behavioral AI Copilot. It observes developer activity inside Visual Studio Code and emits structured `TesseractEvent` JSON messages over a persistent WebSocket connection to the Tesseract Core Engine (Member 4, port 9700).

### Core Principles:
1. Observe developer activity without analyzing, classifying, or judging the user (all intelligence is downstream in Members 4–6).
2. Produce structured, timestamped `TesseractEvent` records with session persistence and monotonic sequence numbers.
3. Preserve contextual details so downstream engines can accurately reconstruct developer activity sequences.
4. Strictly prevent collecting or transmitting secrets, passwords, tokens, API keys, private keys, or complete source-file contents.
5. Minimize duplicate and noisy events using in-memory debouncing and deduplication.
6. Continue functioning offline or when the Core Engine is temporarily unavailable (local circular buffering with active privacy filters).
7. Never noticeably slow down VS Code (<30MB RAM overhead, <2% idle CPU).
8. Gracefully handle unavailable or experimental VS Code APIs.
9. Make sensor state and privacy controls transparent and accessible to the user.
10. Support single-root and multi-root workspaces seamlessly.

---

## 2. Functional Requirements

### FR-1: Editor Activity Tracking
- **FR-1.1**: Detect file open events → emit `file_opened` (`file_path`, `language`, `workspace_folder`, `workspace_name`).
- **FR-1.2**: Detect file save events → emit `file_saved` (`file_path`, `language`, `change_size`, `workspace_folder`).
- **FR-1.3**: Detect file close events → emit `file_closed` (`file_path`, `language`, `duration_ms`, `workspace_folder`).
- **FR-1.4**: Track active editor switches.
- **FR-1.5**: Sample high-frequency edits with configurable debounce interval (`TESSERACT_EDIT_DEBOUNCE_MS=2000` default). No continuous raw cursor tracking.

### FR-2: Error & Diagnostic Detection
- **FR-2.1**: Monitor VS Code diagnostics API (`vscode.languages.onDidChangeDiagnostics`) for errors and warnings.
- **FR-2.2**: Emit `error_detected` with `file_path`, `language`, `error_message`, `error_line`, `severity`, `workspace_folder`.
- **FR-2.3**: Emit `error_resolved` when errors disappear from the diagnostic snapshot.
- **FR-2.4**: Manage the complete appear → persist → resolve error lifecycle without redundant spam.

### FR-3: Terminal Activity Capture
- **FR-3.1**: Detect terminal creation and disposal.
- **FR-3.2**: Capture terminal commands → sanitize secrets/credentials → emit `terminal_command` (`command`, `exit_code`, `duration_ms`, `terminal_name`).
- **FR-3.3**: Sample terminal output (capped at 500 chars, error-focused) → emit `terminal_output` (`output_snippet`, `is_error`).
- **FR-3.4**: Gracefully fall back to `vscode.tasks` API when experimental terminal APIs are unavailable.

### FR-4: Code Execution & Task Detection
- **FR-4.1**: Detect code run via terminal, debug launch, or VS Code tasks.
- **FR-4.2**: Emit `code_executed` with `file_path`, `language`, `command`, `workspace_folder`.

### FR-5: Debug Session Tracking
- **FR-5.1**: Detect debug session start/stop → emit `debug_started`, `debug_ended` with duration.
- **FR-5.2**: Track breakpoint hits → emit `debug_breakpoint_hit` (`file_path`, `line`, `workspace_folder`).

### FR-6: Multi-Root Workspace Context
- **FR-6.1**: Detect workspace folder addition, removal, and active switch → emit `workspace_changed`.
- **FR-6.2**: Tag every event with its corresponding `workspace_folder` identifier.
- **FR-6.3**: Track language composition across all active workspace folders.

### FR-7: Privacy & Sanitization Engine
- **FR-7.1**: Detect and redact API keys, access tokens, bearer tokens, passwords, and private keys.
- **FR-7.2**: Pass all terminal commands through the sanitizer before emission or logging.
- **FR-7.3**: Support configurable file path redaction (workspace-relative or anonymized).
- **FR-7.4**: Prohibit capturing full source code file contents.
- **FR-7.5**: Never log raw, unsanitized events.
- **FR-7.6**: Maintain 100% active privacy protections even when offline.

### FR-8: Session Management & Event Pipeline
- **FR-8.1**: Single persistent `session_id` generated at extension activation; no per-event session churn.
- **FR-8.2**: Monotonically increasing `sequence_number` across all generated events in a session.
- **FR-8.3**: Validate schema and payload size through `EventValidator`.
- **FR-8.4**: Deduplicate noisy identical events within a sliding window via `EventDeduplicator`.
- **FR-8.5**: Health metrics tracking via `HealthMonitor` (generated, sanitized, transmitted, buffered, dropped).

### FR-9: WebSocket Transport & Offline Resiliency
- **FR-9.1**: Persistent WebSocket connection to `ws://localhost:9700/events` with `Authorization: Bearer <secret>`.
- **FR-9.2**: Auto-reconnect with exponential backoff (1s → 2s → 4s ... max 30s).
- **FR-9.3**: Circular event buffer (default 100 max) when offline. Oldest events dropped on overflow with health counter increment.
- **FR-9.4**: Automatic FIFO buffer flush upon server reconnection.

### FR-10: User Controls & Visibility
- **FR-10.1**: Command `tesseract.toggleSensor` to pause/resume observation immediately.
- **FR-10.2**: Command `tesseract.showHealth` to display sensor statistics and diagnostics.
- **FR-10.3**: Status bar indicator showing connection and sensor state (🟢 Connected / 🔴 Offline / ⏸ Paused).

---

## 3. Non-Functional Requirements

| Metric | Target |
|:---|:---|
| Activation Time | < 500ms after VS Code startup |
| Memory Footprint | < 30 MB resident memory overhead |
| CPU Overhead | < 2% idle, < 5% during rapid typing |
| Event Latency | < 50ms from VS Code event to sanitized queue |
| Buffer Capacity | Configurable (default 100 events) |
| Reconnection Backoff | Exponential: 1s → 2s → 4s → ... → 30s max |
| Test Coverage | > 85% on critical paths (sanitizer, transport, trackers) |

---

## 4. Out of Scope

- ❌ Event classification, inference, or learning assessment (Members 4 & 5)
- ❌ WebSocket server hosting (Member 4)
- ❌ Recommendation and tutoring UI (Member 6)
- ❌ Browser activity monitoring (Member 1)
- ❌ OS and filesystem global monitoring (Member 3)
