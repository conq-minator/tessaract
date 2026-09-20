# ⬡ TESSERACT

> **Multimodal, Behavioral AI Copilot for Personalized Learning and Productivity**

[![Status](https://img.shields.io/badge/Status-Phase%200%20%7C%20Architecture%20%26%20Documentation-blue.svg)](#development-phases)
[![Architecture](https://img.shields.io/badge/Architecture-Local--First%20%7C%20Event--Driven-purple.svg)](#architecture)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-20%20LTS%2B-green.svg?logo=node.js)](https://nodejs.org)
[![Runtime](https://img.shields.io/badge/AI%20Runtime-Ollama-orange.svg)](https://ollama.com)
[![License](https://img.shields.io/badge/License-Proprietary%20%2F%20Internal-lightgrey.svg)](#)

---

## 📌 Table of Contents

- [Overview](#-overview)
  - [The Problem](#the-problem)
  - [The Solution](#the-solution)
  - [Key Differentiators](#key-differentiators)
- [Core Capabilities](#-core-capabilities)
  - [1. Activity Observation](#1-activity-observation-permission-controlled)
  - [2. Context & Intent Detection](#2-context--intent-detection)
  - [3. Personal Knowledge Graph (PKG)](#3-personal-knowledge-graph-pkg)
  - [4. Stuck Detector & Friction Scoring](#4-stuck-detector--friction-scoring)
  - [5. Progressive Assistance Framework](#5-progressive-assistance-framework-l1l5)
  - [6. Multimodal Perception](#6-multimodal-perception)
- [System Architecture](#-system-architecture)
  - [Layered Architecture Diagram](#layered-architecture)
  - [Data Flow Pipeline](#data-flow-pipeline)
  - [Service Ports & Communication Matrix](#service-ports--communication-matrix)
  - [Database Architecture](#database-architecture)
  - [Universal Event Schema](#universal-event-schema-tesseractevent)
- [AI & Model Strategy](#-ai--model-strategy)
  - [Deterministic First, AI When Needed](#deterministic-first-ai-when-needed)
  - [Tiered Model Registry](#tiered-model-registry)
  - [OCR & Multimodal Strategy](#ocr--multimodal-strategy)
- [Privacy & Security](#-privacy--security)
  - [Autonomy Levels](#autonomy-levels)
  - [Data Retention Policies](#data-retention-policies)
  - [Zero-Telemetry & Isolation](#zero-telemetry--isolation)
- [Project Structure & Member Ownership](#-project-structure--member-ownership)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Unified Quickstart](#unified-quickstart)
  - [Running Individual Subsystems](#running-individual-subsystems)
- [Development Phases & Roadmap](#-development-phases--roadmap)
- [Code Style & Standards](#-code-style--standards)

---

## 💡 Overview

### The Problem
Existing AI assistants are **fundamentally reactive**. They sit silently waiting for a user prompt, answer in isolation, and immediately forget. They have zero continuous awareness of:
- What the user is actually working on or trying to learn.
- Where friction occurs (e.g., repeated compiler errors, endless tab switching, dead-end searches).
- Missing prerequisite concepts that prevent mastery.
- Repetitive workflows that waste valuable developer and knowledge-worker hours.

Learners spend hours stuck without realizing they lack a foundational concept, while developers repeat identical debugging cycles without actionable behavioral feedback.

### The Solution
**Tesseract** is an ambient, multimodal, behavioral AI copilot for personalized learning and productivity. Operating with explicit user consent, Tesseract observes meaningful activity across digital tools (browser, IDE, terminal, OS, local files) and transforms raw signals into contextual, structured understanding.

It is **not** a chatbot. It does **not** wait for prompts. It:
1. **Observes** structured activity across development environments and browsers.
2. **Understands** user intent and correlates events into coherent learning/work episodes.
3. **Detects friction** deterministically when users hit roadblocks.
4. **Maintains a Personal Knowledge Graph** with evolving skill nodes and confidence scores.
5. **Provides progressive assistance** (hints before full solutions to protect the learning curve).
6. **Constructs adaptive learning roadmaps** tailored to demonstrated knowledge gaps.
7. **Automates repetitive workflows** under human-supervised autonomy guardrails.

### Key Differentiators
- **Behavioral, Not Prompt-Driven**: Derives context passively through observation rather than requiring continuous prompting.
- **Local-First & Private**: Raw telemetry and events remain exclusively on the user's workstation.
- **Progressive Assistance**: Guided discovery and hints first; copy-paste code only as a last resort.
- **Personal Knowledge Graph**: Evolving graph model quantifying mastered vs. developing skills.
- **Lightweight & Efficient**: Deterministic logic handles counters, state machines, and friction scoring; AI is invoked strictly when semantic reasoning is required.

---

## ⚡ Core Capabilities

### 1. Activity Observation (Permission-Controlled)
Tesseract captures **structured events** rather than intrusive, continuous screen video recording:

| Source | Observed Telemetry |
|:---|:---|
| **Firefox / Browser** | Active tab, documentation searches, technical tutorials (e.g., YouTube), navigation flows. |
| **VS Code** | Code edits, file changes, terminal execution, diagnostic error codes, debugging lifecycles. |
| **Terminal / CLI** | Executed commands, exit codes, stderr vs. stdout output. |
| **OS / Window Manager** | Focused application, app switching frequency, idle vs. active task durations. |
| **Local Files** | Project file creation, modification, deletion, and language/type metadata. |
| **Multimodal Inputs** | Screenshots, diagrams, handwritten study notes, mathematical derivations, technical PDFs. |

### 2. Context & Intent Detection
Raw events are aggregated and transformed into coherent **learning episodes**:
```
VS Code: C program compiled ──▶ Compiler Error: Segfault ──▶ Code edited ──▶
Re-compile: Same Error ──▶ Google Search: "pointer dereference segfault" ──▶
YouTube Video: "Pointers in C explained" ──▶ Code fixed ──▶ Successful Build
```
Tesseract recognizes this entire trajectory as a **single targeted learning episode**, mapping the user's struggle directly to pointer concepts.

### 3. Personal Knowledge Graph (PKG)
A persistent NetworkX + SQLite skill graph tracking concepts with dynamic confidence scores:
```
C Programming
│
├── Variables ────────────── Mastered (0.95)
├── Loops ────────────────── Strong (0.85)
├── Functions ────────────── Good (0.75)
├── Arrays ───────────────── Good (0.70)
├── Pointers ─────────────── Weak (0.30)
│   ├── Dereferencing ────── Weak (0.25)
│   ├── NULL handling ────── Developing (0.45)
│   └── Arithmetic ───────── Weak (0.20)
└── Linked Lists ─────────── Developing (0.40)
```
Confidence updates dynamically using Bayesian/heuristic signals: repeated errors, attempt counts, time spent, search patterns, tutorial consumption, and subsequent success.

### 4. Stuck Detector & Friction Scoring
A deterministic, rule-based scoring engine computes friction in real time without unnecessary LLM latency:
$$\text{Repeated Errors} \times 4 + \text{Failed Executions} \times 7 + \text{Searches} \times 3 + \text{Duration} \ge 20\text{m} \implies \mathbf{High\ Friction}$$

### 5. Progressive Assistance Framework (L1–L5)
When high friction is detected, Tesseract intervenes minimally to encourage retention:

```
┌────────────────────────────────────────────────────────┐
│  Level 1: Socratic Hint                                │
│  "Check the memory address allocated before line 42."  │
├────────────────────────────────────────────────────────┤
│  Level 2: Concept Explanation                          │
│  Explains how pointer dereferencing works in C memory. │
├────────────────────────────────────────────────────────┤
│  Level 3: Detailed Breakdown                           │
│  Step-by-step diagnostic of the current code block.    │
├────────────────────────────────────────────────────────┤
│  Level 4: Targeted Practice Problem                    │
│  Small isolated exercise to cement the missing concept.│
├────────────────────────────────────────────────────────┤
│  Level 5: Full Verified Solution                       │
│  Complete patch and implementation explanation.        │
└────────────────────────────────────────────────────────┘
```

### 6. Multimodal Perception
Integrates PaddleOCR and Vision-Language Models (e.g., Gemma 4) to parse screenshots, handwritten whiteboard math, and architectural diagrams directly into structured knowledge.

---

## 🏛 System Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              SYSTEM UI                                  │
│         Web Dashboard · System Tray · Desktop Alert Notifications       │
├─────────────────────────────────────────────────────────────────────────┤
│                       TUTOR & PLANNING ENGINE                           │
│       Progressive Hints (L1-L5) · Adaptive Roadmaps · Recommendations   │
├─────────────────────────────────────────────────────────────────────────┤
│                          AUTOMATION ENGINE                              │
│       Workflow Detection · Pattern Replay Guard · Autonomy Enforcer     │
├─────────────────────────────────────────────────────────────────────────┤
│                      PERSONAL KNOWLEDGE GRAPH                           │
│         Skill Graph (NetworkX + SQLite) · Dynamic Confidence Scores     │
├─────────────────────────────────────────────────────────────────────────┤
│                         AI INFERENCE LAYER                              │
│         Model Abstraction · Local SLM (Ollama) · Cloud Fallback · RAG   │
├─────────────────────────────────────────────────────────────────────────┤
│                     BEHAVIORAL ANALYSIS ENGINE                          │
│       Friction Scorer (Deterministic) · Stuck Detector · Episode Grouper│
├─────────────────────────────────────────────────────────────────────────┤
│                      CONTEXT & INTENT ENGINE                            │
│        Event Correlation · Session Builder · Intent Classifier          │
├─────────────────────────────────────────────────────────────────────────┤
│                       LOCAL EVENT AGGREGATOR                            │
│           Event Bus · Deduplication · Normalization · Buffering         │
├─────────────────────────────────────────────────────────────────────────┤
│                            SENSOR LAYER                                 │
│  ┌────────────────────┬─────────────────────┬────────────────────────┐  │
│  │ Firefox Extension  │  VS Code Extension  │  OS & File System      │  │
│  │ (Member 1)         │  (Member 2)         │  Multimodal (Member 3) │  │
│  └────────────────────┴─────────────────────┴────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Pipeline

```
[Sensors: Browser, VS Code, OS, Multimodal]
                     │
                     ▼  (WebSocket: ws://localhost:9700/events)
        [Local Event Aggregator]
                     │  (Deduplicate, normalize, store into SQLite)
                     ▼
         [Context & Intent Engine]
                     │  (Correlate into Sessions & Learning Episodes)
                     ▼
       [Behavioral Analysis Engine] ──(Deterministic Friction Scoring)
                     │
                     ├──────────────────────────────┐
                     ▼                              ▼
        [Personal Knowledge Graph]        [AI Inference Layer]
        (Skill Nodes & Confidence)        (SLM / Ollama / Cloud Fallback)
                     │                              │
                     └──────────────┬───────────────┘
                                    ▼
                         [Tutor & Planning Engine]
                                    │
                                    ▼  (WebSocket alerts + REST API)
                    [System UI & Dashboard (:9702)]
```

### Service Ports & Communication Matrix

| Service | Port | Protocol | Primary Responsibilities |
|:---|:---|:---|:---|
| **Core Engine** (`member-4`) | `9700` | `ws://localhost:9700/events`<br>`http://localhost:9700/api/v1`<br>`ws://localhost:9700/alerts` | Ingests sensor streams, deduplicates events, runs friction scoring and episode state machines. |
| **AI & Knowledge Service** (`member-5`) | `9701` | `http://localhost:9701/api/v1` | Hosts Ollama abstraction, RAG engine, vector store, and NetworkX Knowledge Graph. |
| **Tutor UI & Dashboard** (`member-6`) | `9702` | `http://localhost:9702` | Web dashboard, interactive tutor chat, knowledge graph visualization, and notifications. |

### Database Architecture
All persistence is **local-first** with zero external cloud database dependencies:
- **Event Store**: Append-only SQLite for raw and structured event replay.
- **Knowledge Graph**: SQLite backing an in-memory NetworkX directed graph.
- **Vector Store**: `sqlite-vec` for local embeddings and semantic RAG retrieval.
- **Full-Text Search**: SQLite FTS5 for local document and code search.
- **Config & Session**: SQLite for user preferences, permissions, and session history.

### Universal Event Schema (`TesseractEvent`)
All sensors emit events conforming to the standard schema:

```json
{
  "event_id": "c4b8a213-39d6-4f7d-8153-2947f6426db1",
  "source": "vscode",
  "event_type": "diagnostic_error",
  "timestamp": "2026-09-20T08:30:00.000Z",
  "payload": {
    "file": "main.c",
    "line": 42,
    "error_code": "E0144",
    "message": "a value of type const char* cannot be used to initialize an entity of type char*"
  },
  "metadata": {
    "session_id": "8f39002b-a49e-4dc3-9c88-e9f0e1329241",
    "confidence": 1.0,
    "privacy_level": "local_only"
  }
}
```

---

## 🧠 AI & Model Strategy

### Deterministic First, AI When Needed
LLMs are expensive in memory, power, and latency. Tesseract strictly adheres to:

```
Rule Engine / Math / State Machine  ──▶  AI Model (Local SLM)  ──▶  Cloud LLM Fallback
(Error count, time, dedup, friction)    (Narrative, intent, hints)   (Complex roadmaps, heavy RAG)
```

| Task | Execution Method | Rationale |
|:---|:---|:---|
| Error repetition & thresholding | Rule-based Counter | Instant, zero overhead |
| Time-on-task calculation | Timestamp Arithmetic | Deterministic |
| Friction / stuck scoring | Weighted Heuristic Engine | Deterministic, transparent |
| Browser tab categorization | URL Pattern + Regex rules | Low latency |
| Intent & episode synthesis | Local SLM (SmolLM2 / Qwen3) | Natural language understanding |
| Personal Knowledge Graph updates | NetworkX graph algorithms | Mathematical confidence tracking |
| Progressive hint generation | Local Reasoning SLM (Gemma 4 / Phi-4) | Balanced reasoning vs speed |
| Multimodal handwriting / OCR | PaddleOCR + Vision SLM | Local vision inference |
| Large-scale curriculum generation | Cloud LLM (Gemini / OpenAI API) | Deep reasoning fallback |

### Tiered Model Registry
Model inference is orchestrated via a unified `ModelRegistry`:
- **Tier 1 (Lightweight / Classification)**: `smollm2:1.7b`, `qwen3:0.6b`, `qwen3:1.7b` (Low footprint, fast).
- **Tier 2 (Reasoning & Tutoring)**: `gemma4:e2b`, `gemma4:e4b`, `phi-4-mini` (On-demand deep reasoning).
- **Tier 3 (Multimodal & Vision)**: `gemma4:e2b/e4b`, `gemma3n` (Visual inspection of code, diagrams).
- **Tier 4 (Cloud Fallback)**: Google Gemini API, OpenAI API (Used strictly with user permission and anonymization).

### OCR & Multimodal Strategy
- **Printed Text & Terminal Screenshots**: PaddleOCR.
- **Handwritten Notes & Math**: PaddleOCR (formula mode) paired with Gemma 4 Vision.
- **Embeddings**: `all-MiniLM-L6-v2` via `sentence-transformers` (~80MB footprint).

---

## 🔒 Privacy & Security

### Autonomy Levels
Tesseract enforces strict autonomy boundaries to protect user intent:

| Level | Mode | Behavior |
|:---:|:---|:---|
| **0** | **Observe** | Passively collect events; zero interventions. |
| **1** | **Understand** | Build context and update Knowledge Graph silently. |
| **2** | **Suggest** | Deliver non-intrusive notifications, hints, and recommendations. |
| **3** | **Prepare** | Stage solutions, pre-fill commands, prepare draft explanations. |
| **4** | **Execute with Approval** | Actions run **only** after explicit user confirmation. |
| **5** | **Autonomous** | Auto-executes reversible, trusted tasks within pre-set scopes. |

> [!IMPORTANT]
> Irreversible actions (financial transactions, file deletions, code commits, sending emails) always enforce **Level 4** (mandatory human approval).

### Data Retention Policies
- **Raw Sensor Events**: Auto-purged after 30 days.
- **Structured Events**: Auto-purged after 90 days.
- **Personal Knowledge Graph**: Persistent local storage (user can export or wipe at any time).
- **Cloud Request Audit Logs**: Auto-purged after 7 days.

### Zero-Telemetry & Isolation
- **No Telemetry**: No behavioral metrics or usage stats leave the user's computer.
- **PII Scrubbing**: Code abstracts and removes file system paths, usernames, and sensitive tokens prior to any optional cloud request.
- **Local SQLite Encryption**: Encrypted on-disk storage with per-installation shared secrets.

---

## 👥 Project Structure & Member Ownership

The codebase is organized into modular components with strict boundaries:

```
tessaract/
├── member-1_browser-sensor/         # [Member 1] Firefox WebExtension (tab, search, video tracking)
├── member-2_vscode-sensor/          # [Member 2] VS Code Extension (code edits, diagnostics, terminal)
├── member-3_os-multimodal-sensor/   # [Member 3] OS watcher, clipboard, PaddleOCR, multimodal ingestion
├── member-4_core-engine/            # [Member 4] Event aggregator, friction scorer, Core API (:9700)
├── member-5_ai-knowledge/           # [Member 5] Ollama abstraction, RAG, Knowledge Graph (:9701)
├── member-6_tutor-ui/               # [Member 6] Dashboard, progressive tutor chat, UI (:9702)
├── scripts/
│   └── run_tesseract.py             # Unified system orchestrator & process supervisor
├── contents.md                      # Master architecture and specifications document
├── instructions.md                  # Development environment and setup guidelines
├── start.bat                        # Windows 1-click launcher
└── stop.bat                         # Windows 1-click clean termination utility
```

### Module Responsibilities

```
┌───────────────────────────────┐       WebSocket       ┌───────────────────────────────┐
│ Member 1: Browser Sensor      │──────────────────────▶│ Member 4: Core Engine (:9700) │
├───────────────────────────────┤   ws://localhost:9700 │  • Event normalization & bus  │
│ Member 2: VS Code Sensor      │──────────────────────▶│  • Deduplication & store      │
├───────────────────────────────┤                       │  • Friction & stuck detector  │
│ Member 3: OS/Multimodal Sensor│──────────────────────▶│  • Session & episode grouping │
└───────────────────────────────┘                       └──────────────┬────────────────┘
                                                                       │ REST & Alert WS
                                        ┌──────────────────────────────┴────────────────┐
                                        ▼                                               ▼
                         ┌───────────────────────────────┐              ┌───────────────────────────────┐
                         │ Member 5: AI & Knowledge      │◀────────────▶│ Member 6: Tutor UI (:9702)    │
                         │ (:9701)                       │  REST API    │  • Progressive Assistance     │
                         │  • Model Registry & Ollama    │              │  • Web Dashboard & Graphs     │
                         │  • Personal Knowledge Graph   │              │  • Interactive Tutor Chat     │
                         │  • Vector Store & Local RAG   │              │  • System Tray & Notifications│
                         └───────────────────────────────┘              └───────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites
- **Operating System**: Windows 10/11 (Ubuntu 22.04+ and macOS supported via abstraction layer).
- **Python**: `3.11+` (3.12 recommended).
- **Node.js**: `20 LTS+` (with `npm 10+`).
- **Ollama**: Installed from [ollama.com](https://ollama.com) and running locally.
- **Git**: `2.40+`.

Verify your runtime installations:
```bash
python --version
node --version
ollama --version
```

Pull the base lightweight model:
```bash
ollama pull smollm2:1.7b
```

---

### Unified Quickstart

The fastest way to launch the complete Tesseract platform:

#### Windows 1-Click Launch:
Double-click `start.bat` or execute in PowerShell:
```cmd
start.bat
```

Or run via Python supervisor directly:
```bash
python scripts/run_tesseract.py --open
```

#### What this does:
1. Validates and clears stale ports (`9700`, `9701`, `9702`).
2. Concurrently boots:
   - **Member 5** (AI & Knowledge Service) on port `9701`
   - **Member 4** (Core Engine) on port `9700`
   - **Member 6** (Tutor UI & Web Dashboard) on port `9702`
3. Automatically opens the dashboard in your default browser.

#### Stopping All Services:
Double-click `stop.bat` or press `Ctrl+C` / type `q` in the runner terminal.

---

### Running Individual Subsystems

During development, members can work in isolation with mocks:

#### 1. Core Engine (Member 4)
```bash
cd member-4_core-engine
python -m venv .venv && .venv\Scripts\activate
pip install -e .
python -m core_engine.main
```

#### 2. AI & Knowledge Service (Member 5)
```bash
cd member-5_ai-knowledge
python -m venv .venv && .venv\Scripts\activate
pip install -e .
python -m src.api.app
```

#### 3. Tutor UI & Web Dashboard (Member 6)
```bash
cd member-6_tutor-ui
python -m venv .venv && .venv\Scripts\activate
pip install -e .
python -m tutor_ui --no-desktop --no-tray
```
*Access the Web UI at:*
- Overview Dashboard: [http://localhost:9702/overview](http://localhost:9702/overview)
- Interactive Knowledge Graph: [http://localhost:9702/knowledge-graph](http://localhost:9702/knowledge-graph)
- AI Tutor Chat: [http://localhost:9702/chat](http://localhost:9702/chat)

#### 4. VS Code Sensor Extension (Member 2)
```bash
cd member-2_vscode-sensor
npm install
npm run compile
# Open folder in VS Code and press F5 to launch the Extension Development Host
```

#### 5. Browser Sensor Extension (Member 1)
```bash
cd member-1_browser-sensor
npm install
npm run build
# In Firefox, navigate to about:debugging -> This Firefox -> Load Temporary Add-on
```

#### 6. OS & Multimodal Sensor (Member 3)
```bash
cd member-3_os-multimodal-sensor
python -m venv .venv && .venv\Scripts\activate
pip install -e .
python -m os_sensor
```

---

## 🗓 Development Phases & Roadmap

| Phase | Title | Focus |
|:---:|:---|:---|
| **Phase 0** | **Architecture & Documentation** | Interface contracts, event schemas, project specifications. |
| **Phase 1** | **Component Isolation** | Independent subsystem development using API stubs & mocks. |
| **Phase 2** | **Interface Integration** | Pairwise contract verification (`M4 ↔ M5`, `M4 ↔ Sensors`, `M4/M5 ↔ M6`). |
| **Phase 3** | **Local End-to-End Pipeline** | Sensor event aggregation through to UI alert delivery. |
| **Phase 4** | **Knowledge & AI Integration** | Dynamic skill graph population, benchmarked SLM tutoring. |
| **Phase 5** | **Behavioral Real-World Testing** | Live debugging and learning workflows under active friction conditions. |
| **Phase 6** | **Privacy & Security Audit** | Verification of local encryption, zero telemetry, and PII redaction. |
| **Phase 7** | **Performance Optimization** | Memory consumption tuning, process idling, lazy model loading. |
| **Phase 8** | **Hackathon / Release Demo** | Polished full-stack demo showcasing socratic learning intervention. |

---

## 📐 Code Style & Standards

- **Python (Members 3, 4, 5, 6)**: Formatted with `black` (line length 100), linted with `ruff`, typed with `mypy --strict`.
- **TypeScript / JavaScript (Members 1, 2, 6)**: Formatted with `prettier`, linted with `eslint`.
- **Git Commit Convention**: `[M{N}] type: short description` (e.g. `[M4] feat: add friction thresholding logic`).
- **Zero Secrets**: API keys and tokens must strictly live in local `.env` files and never be checked into source control.