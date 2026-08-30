# TESSERACT — Master Project Document

> **Last Updated**: 2026-08-30
> **Status**: Phase 0 — Architecture & Documentation
> **Version**: 0.1.0

---

## 1. Product Overview

### 1.1 Product Name

**Tesseract**

### 1.2 Problem

Existing AI assistants are reactive — they wait for a user prompt, answer it, and forget. They have no awareness of what the user is actually doing, what they are trying to learn, where they are struggling, or what assistance would genuinely help.

Learners waste hours stuck on problems without realizing they are missing a prerequisite concept. Developers repeat the same debugging cycles without feedback on their patterns. Knowledge workers perform repetitive workflows manually because no system understands their routines.

### 1.3 Proposed Solution

Tesseract is a **multimodal, behavioral AI copilot for personalized learning and productivity**. It acts as an ambient intelligent layer that, with explicit user permission, observes meaningful activity across digital tools and transforms raw activity into actionable understanding.

It is **not** a chatbot. It does **not** wait for a prompt. It:

- Observes structured events (browser, IDE, terminal, OS, files)
- Understands context (what the user is doing and why)
- Detects friction (when the user is stuck)
- Maps knowledge (what the user knows and what they don't)
- Provides progressive assistance (hints before answers)
- Builds personalized learning roadmaps
- Eventually automates repetitive workflows

### 1.4 Key Differentiators

- **Behavioral, not prompt-driven** — understands user context through observation
- **Local-first** — all raw data stays on the user's machine
- **Progressive assistance** — hints before answers, learning before copy-paste
- **Personal Knowledge Graph** — continuously evolving skill map
- **Lightweight** — deterministic processing first, AI only when reasoning is required

---

## 2. Core Features

### 2.1 Activity Observation (with permission)

| Source | What Tesseract Observes |
|:---|:---|
| Firefox/Browser | Tab activity, searches, YouTube tutorials, navigation patterns |
| VS Code | File edits, code execution, errors, terminal commands, debugging |
| Terminal | Commands, exit codes, output (errors vs success) |
| OS / Applications | Active application, app switching, time spent |
| Local Files | File creation, modification, deletion, type |
| Images | Screenshots, handwritten notes, diagrams |
| Documents | PDFs, notes, mathematical derivations |

The system prioritizes **structured events** over continuous raw surveillance.

### 2.2 Context & Intent Detection

Tesseract transforms raw events into meaningful context:

```
VS Code → C program executed → Compiler error → Code modified →
Program executed again → Same error → Google search → YouTube tutorial →
Another attempt → Successful execution
```

This is understood as a **single learning episode**, not unrelated events.

### 2.3 Personal Knowledge Graph

An evolving skill graph with confidence scores:

```
C Programming
│
├── Variables ────────── Mastered (0.95)
├── Loops ────────────── Strong (0.85)
├── Functions ────────── Good (0.75)
├── Arrays ───────────── Good (0.70)
├── Pointers ─────────── Weak (0.30)
│   ├── Dereferencing ── Weak (0.25)
│   ├── NULL handling ── Developing (0.45)
│   └── Arithmetic ──── Weak (0.20)
└── Linked Lists ─────── Developing (0.40)
```

Updated using **multiple behavioral signals** (repeated errors, attempt count, time spent, search patterns, tutorial consumption, future success). Uses confidence scores, not absolute conclusions.

### 2.4 Stuck Detector

Detects when a user is likely stuck using a friction scoring engine:

```
Same error × 4 + 7 execution attempts + 3 related searches + 20+ minutes + tutorial opened
= HIGH FRICTION → Trigger progressive assistance
```

Progressive assistance levels:

| Level | Action |
|:---|:---|
| L1 | Hint |
| L2 | Concept Explanation |
| L3 | Detailed Breakdown |
| L4 | Practice Problem |
| L5 | Full Solution |

Prioritizes **learning and first-principles understanding** over copy-paste answers.

### 2.5 Personalized Learning

When Tesseract detects a learning activity:

1. Identify the subject
2. Estimate current level
3. Identify prerequisites and missing concepts
4. Analyze consumed resources
5. Build an adaptive roadmap
6. Adjust based on progress and available study time

### 2.6 Multimodal Input

Supports text, images, handwritten notes, mathematical derivations, diagrams, screenshots, code, and documents. Users can submit an image and ask a question — Tesseract determines intent and responds appropriately.

### 2.7 Workflow Intelligence (Future)

Learns repetitive workflow patterns and can automate them with permission. Automation is modular and permission-controlled. Different users/documents remain distinct.

---

## 3. Architecture

### 3.1 Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        SYSTEM UI                            │
│   (System Tray + Web Dashboard + Notifications)             │
├─────────────────────────────────────────────────────────────┤
│                   TUTOR & PLANNING ENGINE                   │
│   (Progressive Assistance · Roadmap · Recommendations)      │
├─────────────────────────────────────────────────────────────┤
│                   AUTOMATION ENGINE                         │
│   (Workflow Detection · Pattern Replay · Permission Guard)  │
├─────────────────────────────────────────────────────────────┤
│               PERSONAL KNOWLEDGE GRAPH                      │
│   (Skill Graph · Confidence Scores · Temporal Evidence)     │
├─────────────────────────────────────────────────────────────┤
│                  AI INFERENCE LAYER                          │
│   (Model Abstraction · Local SLM · Cloud Fallback · RAG)   │
├─────────────────────────────────────────────────────────────┤
│              BEHAVIORAL ANALYSIS ENGINE                     │
│   (Stuck Detector · Friction Scorer · Episode Grouper)      │
├─────────────────────────────────────────────────────────────┤
│           CONTEXT & INTENT ENGINE                           │
│   (Event Correlation · Session Builder · Intent Classifier) │
├─────────────────────────────────────────────────────────────┤
│            LOCAL EVENT AGGREGATOR                            │
│   (Event Bus · Dedup · Normalization · Buffering)           │
├─────────────────────────────────────────────────────────────┤
│                     SENSOR LAYER                            │
│   ┌──────────┬──────────┬──────────────────────┐           │
│   │ Firefox  │ VS Code  │ OS / Files / Multi-  │           │
│   │Extension │Extension │ modal Monitors       │           │
│   └──────────┴──────────┴──────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

```
Raw Sensor Events (browser tabs, editor keystrokes, file changes…)
    ↓
Local Event Aggregator (normalize, deduplicate, buffer)
    ↓
Structured Events (TesseractEvent schema)
    ↓
Context & Intent Engine (correlate events → sessions → episodes)
    ↓
Behavioral Analysis Engine (stuck detection, friction scoring — DETERMINISTIC)
    ↓
Personal Knowledge Graph (update skill nodes, confidence scores)
    ↓
AI Inference Layer (only when reasoning is actually required)
    ↓
Tutor / Planning Engine (progressive hints, roadmaps, recommendations)
    ↓
System UI (notifications, dashboard, approval dialogs)
```

### 3.3 Communication

| Channel | Protocol | Purpose |
|:---|:---|:---|
| Sensor → Core Engine | WebSocket (`ws://localhost:9700/events`) | Real-time event streaming |
| Core Engine internals | In-process async queues | Aggregator → Context → Behavioral |
| Core Engine → AI Layer | REST (`http://localhost:9701/api/v1`) | Inference requests |
| Core Engine → UI | REST + WebSocket (`ws://localhost:9700/alerts`) | Data queries + real-time alerts |
| UI → AI Layer | REST (`http://localhost:9701/api/v1`) | Tutor/roadmap requests |

The core engine runs as a **single Python process**. Only the sensors (browser extension, VS Code extension) and UI are separate processes.

### 3.4 Database Architecture

| Store | Technology | Purpose |
|:---|:---|:---|
| Event Store | SQLite (append-only) | Raw and structured events |
| Knowledge Graph | SQLite + NetworkX (in-memory) | Skill nodes, edges, confidence scores |
| Vector Store | sqlite-vec | Embeddings for RAG, semantic search |
| Session/Config | SQLite | User preferences, autonomy levels, model configs |
| File Index | SQLite + FTS5 | Full-text search over local documents |

All databases are **local SQLite files** — zero server infrastructure required.

### 3.5 Port Assignments

| Port | Service | Owner |
|:---|:---|:---|
| 9700 | Core Engine (WebSocket server + REST API) | Member 4 |
| 9701 | AI & Knowledge Service (REST API) | Member 5 |
| 9702 | Tutor/UI Web Dashboard (HTTP) | Member 6 |

---

## 4. AI Architecture

### 4.1 Don't Use an LLM for Everything

| Task | Processing Method |
|:---|:---|
| Repeated error counting | Counter / rule-based |
| Time-on-task calculation | Timestamps + arithmetic |
| App switching detection | OS API + state machine |
| File type classification | MIME type + extension map |
| Event deduplication | Hash + time window |
| Friction/stuck scoring | Weighted rule engine |
| Browser tab categorization | URL pattern + lightweight classifier |
| Intent classification | Local SLM (when patterns insufficient) |
| Episode narrative synthesis | Local SLM |
| Complex concept mapping | Local SLM or cloud |
| Roadmap generation | Cloud LLM (fallback) |
| Handwritten note understanding | Local VLM |
| Advanced multimodal QA | Cloud LLM (fallback) |

**Use AI where reasoning is actually required. Use deterministic code everywhere else.**

### 4.2 Model Abstraction Layer

Every AI call goes through a `ModelRegistry`. Models are assigned per-task and can be swapped without touching any other code. The registry supports:

- Multiple model tiers (lightweight, reasoning, multimodal, cloud)
- Lazy loading and idle unloading
- Automatic fallback (local → cloud)
- Per-task model assignment
- Benchmark-driven selection

### 4.3 Model Benchmark Candidates

**Tier 1 — Lightweight Event/Classification** (always loaded, small footprint):
- SmolLM2 1.7B (1.7B params, 8K context, ~1 GB Q4)
- Qwen3-0.6B (0.6B params, 32K context, ~0.5 GB Q4)
- Qwen3-1.7B (1.7B params, 32K context, ~1.2 GB Q4)

**Tier 2 — Main Local Reasoning** (loaded on demand):
- Gemma 4 E2B (~2B effective / 5.1B MoE, 128K context, multimodal, Apache 2.0)
- Gemma 4 E4B (~4B effective / 8B MoE, 128K context, multimodal, Apache 2.0)
- Phi-4 mini (3.8B dense, 128K context, MIT)

**Tier 3 — Multimodal/Vision** (loaded on demand):
- Gemma 4 E2B/E4B (text + image + audio, Apache 2.0)
- Gemma 3n E2B/E4B (text + image + video + audio, 32K context)

**Tier 4 — Cloud Fallback** (API calls, never loaded locally):
- Google Gemini API
- OpenAI API

> **Benchmark-first strategy**: Choose the smallest model that provides acceptable quality. Do not choose a model solely because it has more parameters. If a newer, faster, more accurate model becomes available, replace candidates freely.

### 4.4 Model Runtime

**Ollama** — manages model downloads, quantization, loading/unloading, and exposes an OpenAI-compatible REST API. Supports all candidate models.

### 4.5 OCR Strategy

| Input Type | Tool |
|:---|:---|
| Printed text / screenshots | PaddleOCR |
| Handwritten notes | PaddleOCR + VLM (Gemma 4 E2B) |
| Mathematical formulas | PaddleOCR (formula mode) + VLM |
| Technical diagrams | VLM (Gemma 4 E2B/E4B) |

### 4.6 Embedding Model

**all-MiniLM-L6-v2** (22M params, 384-dim, ~80 MB) via sentence-transformers. Upgradeable if benchmarks show insufficient quality.

---

## 5. Local/Cloud Strategy

### 5.1 Local Processing (default)

- Event collection and normalization
- OCR and document indexing
- Sensitive information processing
- Memory and embeddings
- Lightweight inference (classification, intent, friction scoring)
- Behavioral analysis
- Knowledge graph maintenance

### 5.2 Cloud Processing (only when necessary)

- Complex multi-step reasoning
- Large-scale roadmap generation
- Advanced multimodal reasoning (complex diagrams, multi-page documents)
- Heavy AI workloads exceeding local hardware

### 5.3 Cloud Request Minimization

1. Strip PII before sending
2. Abstract context (send "struggling with C pointer dereferencing" not raw code)
3. Batch multiple questions into one API call
4. Cache cloud responses locally

---

## 6. Privacy & Security

### 6.1 Autonomy Levels

| Level | Name | Capability |
|:---|:---|:---|
| 0 | Observe | Collect events silently |
| 1 | Understand | Build context, update knowledge graph |
| 2 | Suggest | Show notifications, hints, recommendations |
| 3 | Prepare | Draft responses, pre-fill forms, stage actions |
| 4 | Execute with Approval | Perform actions only after explicit user confirmation |
| 5 | Autonomous | Execute trusted, pre-approved, reversible actions only |

Consequential/irreversible actions (tax submissions, financial transactions, sending emails, deleting files, publishing) **must always require explicit human approval**.

### 6.2 Data Retention (defaults, user-configurable)

- Raw events: 30 days → auto-purge
- Structured events: 90 days → auto-purge
- Knowledge graph: Persistent (user can export/delete)
- Embeddings: Persistent (rebuilt on demand)
- Cloud request logs: 7 days → auto-purge

### 6.3 Security Rules

- All data stored locally in encrypted SQLite databases
- No telemetry or usage data sent externally
- API keys stored in local `.env` files, never committed to Git
- Cloud requests use HTTPS with API key authentication
- User can pause/stop observation at any time
- User can view, export, and delete all collected data

---

## 7. Six-Member Division

### 7.1 Responsibility Matrix

| Member | Folder | Responsibility |
|:---|:---|:---|
| Member 1 | `member-1_browser-sensor` | Firefox WebExtension — browser activity observation |
| Member 2 | `member-2_vscode-sensor` | VS Code Extension — developer activity observation |
| Member 3 | `member-3_os-multimodal-sensor` | OS monitoring, file watching, OCR, multimodal input |
| Member 4 | `member-4_core-engine` | Event Aggregator + Context Engine + Behavioral Analyzer + Stuck Detector |
| Member 5 | `member-5_ai-knowledge` | AI Inference Layer + Knowledge Graph + Model Abstraction + Benchmarking |
| Member 6 | `member-6_tutor-ui` | Tutor/Planning Engine + Recommendation + UI + Automation Engine |

### 7.2 Ownership Rules

- **NO TEAM MEMBER MAY MODIFY ANOTHER MEMBER'S FOLDER**
- If a member requires another component, they use its documented interface
- They do not modify its implementation
- This prevents Git conflicts and overlapping work

### 7.3 Component Ownership

```
Firefox WebExtension ─────────────── Member 1
  Tab tracking, URL/search monitoring, YouTube detection,
  page content extraction, WebSocket event emitter

VS Code Extension ────────────────── Member 2
  Editor activity, terminal capture, error/diagnostic detection,
  build/run events, WebSocket event emitter

OS/Multimodal Sensor ─────────────── Member 3
  File system watcher, app usage monitor, screenshot/clipboard,
  OCR pipeline (PaddleOCR), image/document ingestion,
  WebSocket event emitter

Core Engine ──────────────────────── Member 4
  WebSocket event receiver (server), event normalization & dedup,
  event store (SQLite), session builder, episode grouper,
  intent classifier (rule-based), stuck detector (rule-based),
  friction scorer, behavioral analysis engine,
  REST API for downstream consumers

AI & Knowledge ───────────────────── Member 5
  Model abstraction layer, model registry & config,
  Ollama integration, cloud API integration, benchmark suite,
  embedding pipeline, vector store (sqlite-vec), RAG engine,
  Personal Knowledge Graph (NetworkX + SQLite),
  skill node management, confidence scoring, concept mapping

Tutor & UI ───────────────────────── Member 6
  Progressive assistance engine (L1–L5), hint generator,
  roadmap builder, recommendation engine, learning resource
  aggregator, automation engine, permission guard (autonomy levels),
  system tray application, web dashboard, notification system,
  approval dialogs
```

---

## 8. Interface Contracts

### 8.1 Universal Event Schema (TesseractEvent)

```json
{
  "event_id": "uuid-v4",
  "source": "browser | vscode | os | file | multimodal | user",
  "event_type": "string",
  "timestamp": "ISO-8601",
  "payload": {},
  "metadata": {
    "session_id": "uuid-v4",
    "confidence": 0.0,
    "privacy_level": "local_only | abstractable | cloud_safe"
  }
}
```

### 8.2 Sensor → Core Engine (WebSocket)

- **Endpoint**: `ws://localhost:9700/events`
- **Owner**: Member 4
- **Consumers**: Members 1, 2, 3
- **Direction**: Sensor → Core Engine (push)
- **Auth**: Local shared secret from `.env`

### 8.3 Core Engine → AI Layer (REST)

- **Base URL**: `http://localhost:9701/api/v1`
- **Owner**: Member 5
- **Consumers**: Members 4, 6
- **Key endpoints**: `/inference/complete`, `/inference/classify`, `/inference/vision`, `/inference/embed`, `/knowledge/update`, `/knowledge/graph`, `/knowledge/query`

### 8.4 Core Engine → Tutor/UI (REST + WebSocket)

- **REST**: `http://localhost:9700/api/v1`
- **WebSocket**: `ws://localhost:9700/alerts`
- **Owner**: Member 4
- **Consumer**: Member 6
- **Key endpoints**: `/events/recent`, `/sessions/active`, `/episodes/recent`, `/friction/current`, `/context/current`

### 8.5 Tutor/UI → AI Layer (REST)

- **Base URL**: `http://localhost:9701/api/v1`
- **Owner**: Member 5
- **Consumer**: Member 6
- **Key endpoints**: `/tutor/hint`, `/tutor/explain`, `/tutor/practice`, `/tutor/roadmap`, `/tutor/recommend`

### 8.6 Interface Summary

```
┌──────────┐  WS   ┌──────────────┐  REST  ┌───────────────┐
│ Member 1 │──────→│              │──────→│               │
│ Browser  │       │              │       │   Member 5    │
├──────────┤  WS   │  Member 4    │  REST  │   AI &        │
│ Member 2 │──────→│  Core Engine │←──────│   Knowledge   │
│ VS Code  │       │              │       │               │
├──────────┤  WS   │  Port 9700   │       │   Port 9701   │
│ Member 3 │──────→│              │       │               │
│ OS/Multi │       └──────┬───────┘       └───────┬───────┘
└──────────┘              │                       │
                     REST + WS                   REST
                          │                       │
                          ↓                       │
                   ┌──────────────┐               │
                   │   Member 6   │←──────────────┘
                   │   Tutor/UI   │
                   │   Port 9702  │
                   └──────────────┘
```

---

## 9. Dependencies Between Members

```
Member 1 (Browser)    ──depends on──→  Member 4 (Core Engine WebSocket server)
Member 2 (VS Code)    ──depends on──→  Member 4 (Core Engine WebSocket server)
Member 3 (OS/Multi)   ──depends on──→  Member 4 (Core Engine WebSocket server)
Member 4 (Core Engine) ──depends on──→  Member 5 (AI inference API)
Member 6 (Tutor/UI)   ──depends on──→  Member 4 (Core Engine data API)
Member 6 (Tutor/UI)   ──depends on──→  Member 5 (AI tutor/knowledge API)
```

**No circular dependencies.** Members 1–3 depend only on Member 4. Member 4 depends only on Member 5. Member 6 depends on both 4 and 5.

During Phase 1 (independent development), all members use **mocks/stubs** for their dependencies.

---

## 10. Development Phases

| Phase | Name | Duration | Key Deliverables |
|:---|:---|:---|:---|
| 0 | Architecture & Documentation | Week 1 | This document, all member docs, interface specs |
| 1 | Independent Component Development | Weeks 2–5 | Each member builds with mocks |
| 2 | Interface Testing | Week 6 | Pairwise integration tests |
| 3 | Local Integration | Weeks 7–8 | Full pipeline end-to-end |
| 4 | AI + Knowledge Graph Integration | Weeks 8–10 | Model benchmarking, KG population, tutoring |
| 5 | End-to-End Behavioral Testing | Weeks 10–11 | Real usage scenarios |
| 6 | Privacy & Security Testing | Week 12 | Data isolation, PII stripping audit |
| 7 | Performance Optimization | Week 13 | Memory, battery, lazy loading |
| 8 | Hackathon Demo Build | Week 14 | Polished demo |

---

## 11. Testing Strategy

- **Unit tests**: Each member writes tests for their own component
- **Integration tests**: Pairwise tests using real interfaces (Phase 2)
- **End-to-end tests**: Full pipeline from sensor event to UI notification (Phase 5)
- **Benchmark tests**: AI model evaluation suite (Phase 4)
- **Privacy tests**: Verify no PII leaks to cloud, data retention enforced (Phase 6)
- **Performance tests**: Memory profiling, latency measurement, battery impact (Phase 7)

---

## 12. Integration Strategy

1. Members 1–3 connect to Member 4's WebSocket server
2. Member 4 connects to Member 5's REST API
3. Member 6 connects to both Member 4 (data) and Member 5 (AI)
4. Integration proceeds in dependency order: M5 → M4 → M1/M2/M3 → M6

---

## 13. Future Roadmap

- **Android support**: Architecture supports mobile via Model Abstraction Layer (same interface, different model — e.g., Gemma 4 E2B on mobile)
- **Workflow automation**: Modular, permission-controlled (post-MVP)
- **Additional sensors**: Slack, Discord, email, calendar
- **Team/classroom mode**: Aggregate anonymized skill gaps across a cohort
- **Plugin system**: Third-party sensor and tutor plugins
