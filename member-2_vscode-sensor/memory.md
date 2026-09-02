# Member 2 — VS Code Sensor: Memory & Decision Log

> **Owner**: Member 2  
> **Last Updated**: 2026-08-31  
> **Purpose**: Persistent memory of decisions, learnings, blockers, and architectural context.

---

## Decision Log

| # | Date | Decision | Rationale |
|:---|:---|:---|:---|
| D-001 | 2026-08-31 | Use TypeScript strict mode (ES2022/CommonJS) | Enforces type safety, aligns with VS Code extension standards |
| D-002 | 2026-08-31 | Use `ws` npm package for transport | Supports custom `Authorization` handshake headers reliably in Node.js |
| D-003 | 2026-08-31 | Multi-root workspace support (DECIDED: YES) | All events tagged with `workspace_folder`; works seamlessly with single-root |
| D-004 | 2026-08-31 | 2000 ms debounce for high-frequency editor events | Prevents event flooding, configurable via `TESSERACT_EDIT_DEBOUNCE_MS` |
| D-005 | 2026-08-31 | Single `session_id` per extension lifecycle | Managed by `SessionManager`; prevents session churn and enables session tracking |
| D-006 | 2026-08-31 | Monotonically increasing `sequence_number` | Allows downstream Core Engine (M4) to detect lost or out-of-order events |
| D-007 | 2026-08-31 | Proactive Privacy Sanitizer in pipeline | Redacts API keys, bearer tokens, passwords, SSH keys, terminal commands, and file paths before buffering or transmitting |
| D-008 | 2026-08-31 | Event Validator & Deduplicator before transport | Filters out schema violations, oversized payloads, and rapid duplicate noise |
| D-009 | 2026-08-31 | Health Monitor with event counters | Tracks generated, sanitized, transmitted, buffered, and dropped metrics |
| D-010 | 2026-08-31 | Circular buffer (max 100) with FIFO overflow | Prevents memory leaks during Core Engine outages; oldest dropped with counter |
| D-011 | 2026-08-31 | Terminal output capped at 500 chars (error-focused) | Keeps payload compact; captures essential error snippets |
| D-012 | 2026-08-31 | Experimental API fallback strategy | Graceful fallback to `vscode.tasks` API when `onDidWriteTerminalData` is unavailable |

---

## Key Learnings & Architecture Patterns

1. **Pipeline Order**: `Tracker -> EventFactory (session/seq) -> PrivacySanitizer -> EventValidator -> EventDeduplicator -> HealthMonitor -> WebSocketClient (Buffer) -> Wire`.
2. **Safe Logging**: Raw events are never logged to console or OutputChannel; only sanitized and summarized metadata is logged.
3. **Multi-Root Resolution**: Use `vscode.workspace.getWorkspaceFolder(document.uri)` to dynamically map documents to their workspace root.
4. **Diagnostic Snapshot Diffing**: Compare current diagnostic array with cached state to emit distinct `error_detected` and `error_resolved` events without spamming.
5. **Clean Disposal**: All VS Code event listeners, intervals, and WebSocket sockets register into `ExtensionContext.subscriptions`.

---

## Configuration Reference

| Variable | Default | Description |
|:---|:---|:---|
| `TESSERACT_CORE_WS_URL` | `ws://localhost:9700/events` | WebSocket endpoint of Member 4 Core Engine |
| `TESSERACT_SHARED_SECRET` | (empty string) | Bearer token for WebSocket handshake authentication |
| `TESSERACT_BUFFER_SIZE` | `100` | Max number of events to queue offline before dropping |
| `TESSERACT_RECONNECT_INTERVAL_MS` | `5000` | Base interval for exponential backoff reconnection |
| `TESSERACT_EDIT_DEBOUNCE_MS` | `2000` | Debounce threshold for high-frequency editor events |
| `TESSERACT_TERMINAL_CAPTURE` | `true` | Enable/disable terminal command and output observation |
| `TESSERACT_PATH_REDACTION` | `relative` | File path format: `relative` to workspace, `full`, or `anonymized` |
| `TESSERACT_LOG_LEVEL` | `DEBUG` | Log level for VS Code output channel |

---

## Rules to Enforce

1. **Folder Discipline**: Only touch files within `member-2_vscode-sensor/`.
2. **Zero AI Models**: Member 2 is a pure deterministic sensor.
3. **Commit Standard**: `[M2] type: short description`.
4. **Branch Standard**: `member-2/{type}-{description}`.
