# Member 2 — VS Code Sensor: Development Phases

> **Owner**: Member 2  
> **Last Updated**: 2026-08-31  
> **Current Phase**: Phase 0 → Phase 1A (Scaffold)

---

## Phase Overview

| Phase | Name | Status | Start | End |
|:---|:---|:---|:---|:---|
| **0** | Architecture & Documentation | ✅ Complete | 2026-08-31 | 2026-08-31 |
| **1A** | Project Scaffold & Configuration | ⬜ Not Started | — | — |
| **1B** | Types, Session & Privacy Utilities | ⬜ Not Started | — | — |
| **1C** | Sensor Trackers | ⬜ Not Started | — | — |
| **1D** | Event Pipeline & WebSocket Transport | ⬜ Not Started | — | — |
| **1E** | Extension Entry & User Controls | ⬜ Not Started | — | — |
| **1F** | Unit + Integration Tests | ⬜ Not Started | — | — |
| **1G** | Documentation & Packaging | ⬜ Not Started | — | — |
| **1H** | Production Readiness Audit | ⬜ Not Started | — | — |
| **2** | Interface Testing (with Member 4) | ⬜ Not Started | — | — |
| **3** | Local Integration (End-to-End) | ⬜ Not Started | — | — |

---

## Phase 0 — Architecture & Documentation ✅

**Deliverables:**
- [x] `contents.md` — Component specification & event contracts
- [x] `instructions.md` — Development and setup instructions
- [x] `prd.md` — Product requirements document with privacy & multi-root support
- [x] `memory.md` — Decision & learning memory log
- [x] `phases.md` — Phase tracking document
- [x] Implementation plan updated and aligned with full privacy architecture

---

## Phase 1A — Project Scaffold & Configuration ⬜

**Goal**: Set up extension project configuration, dependencies, and build pipeline.

**Deliverables:**
- [ ] `package.json` — Manifest with commands, settings, dependencies, engines
- [ ] `tsconfig.json` — TypeScript strict ES2022/CommonJS config
- [ ] `.eslintrc.json` — ESLint rules
- [ ] `.prettierrc` — Prettier rules
- [ ] `.vscodeignore` — Extension packaging filter
- [ ] `.vscode/launch.json` & `tasks.json` — F5 debug configuration
- [ ] Run `npm install` and verify zero vulnerabilities

---

## Phase 1B — Types, Session & Privacy Utilities ⬜

**Goal**: Implement data types, session management, sanitization, validation, deduplication, and metrics.

**Deliverables:**
- [ ] `src/types/events.ts` & `src/types/config.ts` — Complete schema & config types
- [ ] `src/session/session-manager.ts` — Persistent session ID & monotonic sequence numbering
- [ ] `src/utils/sanitizer.ts` — Secrets, tokens, passwords, command, and path redaction
- [ ] `src/utils/event-validator.ts` — Schema validation & payload size enforcement
- [ ] `src/utils/event-deduplicator.ts` — Time-window noise filter
- [ ] `src/utils/health-monitor.ts` — Metrics counters for pipeline events
- [ ] `src/utils/logger.ts` — Privacy-safe logging to VS Code OutputChannel
- [ ] `src/utils/event-factory.ts` — Standardized event generation

---

## Phase 1C — Sensor Trackers ⬜

**Goal**: Implement VS Code event observation modules with multi-root support.

**Deliverables:**
- [ ] `src/trackers/editor-tracker.ts` — Opens, closes, saves, active switch, debounced typing
- [ ] `src/trackers/diagnostic-watcher.ts` — Error detection, snapshot diffing, error resolution
- [ ] `src/trackers/terminal-monitor.ts` — Command execution, exit codes, output sampling (fallback safe)
- [ ] `src/trackers/debug-tracker.ts` — Debug sessions, breakpoint hits
- [ ] `src/trackers/workspace-tracker.ts` — Multi-root folders, language composition

---

## Phase 1D — Event Pipeline & WebSocket Transport ⬜

**Goal**: Implement resilient WebSocket client and central event processing pipeline.

**Deliverables:**
- [ ] `src/transport/websocket-client.ts` — Connection, bearer auth, circular buffer, exponential reconnect
- [ ] `src/transport/event-emitter.ts` — Pipeline: `Tracker -> Factory -> Sanitizer -> Validator -> Deduplicator -> Health -> Client`

---

## Phase 1E — Extension Entry & User Controls ⬜

**Goal**: Wire extension lifecycle, user toggle command, and health status indicators.

**Deliverables:**
- [ ] `src/extension.ts` — activate/deactivate, subscription cleanup
- [ ] Commands: `tesseract.toggleSensor`, `tesseract.showHealth`
- [ ] Status bar UI: Connection state (🟢 / 🔴 / ⏸)

---

## Phase 1F — Unit + Integration Tests ⬜

**Goal**: Comprehensive automated testing of all units and full event pipeline.

**Deliverables:**
- [ ] `src/test/suite/privacy-sanitizer.test.ts`
- [ ] `src/test/suite/event-validator.test.ts`
- [ ] `src/test/suite/session-manager.test.ts`
- [ ] `src/test/suite/event-deduplicator.test.ts`
- [ ] `src/test/suite/health-monitor.test.ts`
- [ ] `src/test/suite/editor-tracker.test.ts`
- [ ] `src/test/suite/diagnostic-watcher.test.ts`
- [ ] `src/test/suite/terminal-monitor.test.ts`
- [ ] `src/test/suite/websocket-client.test.ts`
- [ ] `src/test/integration/pipeline.test.ts`
- [ ] `src/test/runTest.ts`
- [ ] `npm test` passing with 100% success

---

## Phase 1G — Documentation & Packaging ⬜

**Goal**: Complete documentation and produce distributable `.vsix` extension package.

**Deliverables:**
- [ ] `README.md` — Installation, configuration, architecture, privacy guarantees
- [ ] `npx @vscode/vsce package` — Valid `.vsix` built successfully
- [ ] Synchronized `prd.md`, `memory.md`, `phases.md`

---

## Phase 1H — Production Readiness Audit ⬜

**Goal**: Comprehensive audit across all production quality dimensions.

**Audit Checklist:**
- [ ] **Privacy**: Redaction verification on credentials, keys, passwords, and commands
- [ ] **Security**: No hardcoded secrets, safe logging only, auth header handshake
- [ ] **Performance**: VS Code remains responsive under rapid typing stress; memory <30MB
- [ ] **WebSocket & Offline**: Circular buffer overflow policy verified; smooth reconnect and flush
- [ ] **Multi-Root**: Correct workspace identification across multi-folder setups
- [ ] **API Compatibility**: Graceful fallback for experimental terminal APIs
- [ ] **Health Monitoring**: Generated, transmitted, buffered, and dropped metrics accurate
- [ ] **Test Coverage**: All test suites green

---

## Phase 2 — Interface Testing (with Member 4) ⬜
- Connect extension to live Member 4 Core Engine (`ws://localhost:9700/events`).

## Phase 3 — Local Integration (End-to-End) ⬜
- Full system verification across all 6 members.
