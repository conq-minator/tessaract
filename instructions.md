# TESSERACT — Global Development Instructions

> **Last Updated**: 2026-08-30
> **Status**: Phase 0 — Architecture & Documentation

---

## 1. Supported Operating Systems

| OS | Status | Notes |
|:---|:---|:---|
| **Windows 10/11** | Primary | All members must support |
| **Ubuntu 22.04+ / Debian 12+** | Secondary | Support planned from Phase 3 |
| **macOS 13+** | Secondary | Support planned from Phase 3 |

All development and testing should initially target **Windows**. Platform-specific code (Member 3 — OS APIs) must use abstraction layers to support other platforms later.

---

## 2. Required Software

### 2.1 Python

| Requirement | Version |
|:---|:---|
| Python | **3.11+** (3.12 recommended) |
| pip | Latest |
| venv | Built-in (use for all Python projects) |

All Python members (3, 4, 5, 6) must use **virtual environments**. Never install packages globally.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

### 2.2 Node.js

| Requirement | Version |
|:---|:---|
| Node.js | **20 LTS+** (22 LTS recommended) |
| npm | **10+** (comes with Node.js) |

Required by Members 1 (Firefox extension build tools) and 2 (VS Code extension).

### 2.3 Git

| Requirement | Version |
|:---|:---|
| Git | **2.40+** |

### 2.4 Browser

| Requirement | Version |
|:---|:---|
| Firefox | **128+** (latest ESR or Release) |
| Firefox Developer Edition | Recommended for extension debugging |

Required by Member 1.

### 2.5 VS Code

| Requirement | Version |
|:---|:---|
| VS Code | **1.90+** (latest stable) |
| VS Code Insiders | Recommended for extension development |

Required by Member 2.

### 2.6 Ollama (Local AI Runtime)

| Requirement | Version |
|:---|:---|
| Ollama | **Latest stable** |

Required by Member 5. Install from [ollama.com](https://ollama.com).

```bash
# Verify installation
ollama --version

# Pull a test model
ollama pull smollm2:1.7b
```

### 2.7 C/C++ (Optional)

Only required if PaddleOCR needs to be built from source (Member 3). Pre-built wheels are preferred.

| Requirement | Version |
|:---|:---|
| MSVC Build Tools | 2022+ (Windows) |
| GCC | 12+ (Linux) |

### 2.8 Database

No external database server is required. **SQLite** is embedded in Python's standard library. Additional extensions:

| Package | Purpose | Required By |
|:---|:---|:---|
| `sqlite-vec` | Vector similarity search | Member 5 |
| SQLite FTS5 | Full-text search | Members 4, 5 |

---

## 3. Environment Variables

### 3.1 Global Variables (all members)

```env
# Tesseract Core
TESSERACT_ENV=development
TESSERACT_LOG_LEVEL=DEBUG
TESSERACT_DATA_DIR=~/.tesseract/data

# Inter-service Communication
TESSERACT_CORE_HOST=localhost
TESSERACT_CORE_PORT=9700
TESSERACT_AI_HOST=localhost
TESSERACT_AI_PORT=9701
TESSERACT_UI_PORT=9702
TESSERACT_SHARED_SECRET=

# Privacy
TESSERACT_CLOUD_ENABLED=false
TESSERACT_RAW_EVENT_RETENTION_DAYS=30
TESSERACT_STRUCTURED_EVENT_RETENTION_DAYS=90
```

### 3.2 Member-Specific Variables

See each member's `env/member-X/.env.example` for member-specific variables.

### 3.3 Security Rules for Environment Variables

- **NEVER** commit real API keys, passwords, tokens, or secrets to Git
- Use `.env.example` files with empty values as templates
- Real `.env` files must be in `.gitignore`
- Each developer creates their own `.env` locally from the `.env.example`

---

## 4. Installation Instructions

### 4.1 Clone the Repository

```bash
git clone <repository-url> TESSERACT
cd TESSERACT
```

### 4.2 Set Up Environment Variables

```bash
# Copy the global .env.example (when created)
# Copy member-specific .env.example files to .env
# Fill in your personal API keys and secrets
```

### 4.3 Member-Specific Setup

Each member folder contains its own `instructions.md` with detailed setup steps. Follow those for your specific component:

- [Member 1 Instructions](member-1_browser-sensor/instructions.md)
- [Member 2 Instructions](member-2_vscode-sensor/instructions.md)
- [Member 3 Instructions](member-3_os-multimodal-sensor/instructions.md)
- [Member 4 Instructions](member-4_core-engine/instructions.md)
- [Member 5 Instructions](member-5_ai-knowledge/instructions.md)
- [Member 6 Instructions](member-6_tutor-ui/instructions.md)

---

## 5. Build Instructions

There is no single global build command. Each member builds independently:

| Member | Build Command | Language |
|:---|:---|:---|
| 1 | `npm run build` (produces `.xpi`) | JavaScript |
| 2 | `npm run compile` (produces `.vsix`) | TypeScript |
| 3 | `pip install -e .` | Python |
| 4 | `pip install -e .` | Python |
| 5 | `pip install -e .` | Python |
| 6 | `pip install -e .` (backend) + `npm run build` (frontend) | Python + JS |

---

## 6. Test Instructions

Each member runs their own tests:

| Member | Test Command | Framework |
|:---|:---|:---|
| 1 | `npm test` | Jest / web-ext lint |
| 2 | `npm test` | Mocha / VS Code test runner |
| 3 | `pytest` | pytest |
| 4 | `pytest` | pytest |
| 5 | `pytest` | pytest |
| 6 | `pytest` (backend) + `npm test` (frontend) | pytest + Jest |

### Integration Tests (Phase 2+)

```bash
# Run from the project root after all services are running
pytest tests/integration/ -v
```

---

## 7. Run Instructions

### 7.1 Development Mode (Individual Members)

Each member can run independently using mocks:

```bash
# Member 4 (Core Engine — start this first)
cd member-4_core-engine
python -m venv .venv && .venv\Scripts\activate
pip install -e .
python -m core_engine --mock-ai

# Member 5 (AI & Knowledge)
cd member-5_ai-knowledge
python -m venv .venv && .venv\Scripts\activate
pip install -e .
python -m ai_knowledge

# Member 6 (Tutor/UI)
cd member-6_tutor-ui
python -m venv .venv && .venv\Scripts\activate
pip install -e .
python -m tutor_ui

# Member 1 (Firefox Extension — load temporarily in Firefox)
cd member-1_browser-sensor
npm install && npm run build
# Load in Firefox: about:debugging → Load Temporary Add-on

# Member 2 (VS Code Extension)
cd member-2_vscode-sensor
npm install && npm run compile
# Press F5 in VS Code to launch Extension Development Host

# Member 3 (OS/Multimodal Sensor)
cd member-3_os-multimodal-sensor
python -m venv .venv && .venv\Scripts\activate
pip install -e .
python -m os_sensor
```

### 7.2 Full System (Phase 3+)

Start services in dependency order:

```bash
# 1. Start AI & Knowledge Service
cd member-5_ai-knowledge && python -m ai_knowledge

# 2. Start Core Engine
cd member-4_core-engine && python -m core_engine

# 3. Start Tutor/UI
cd member-6_tutor-ui && python -m tutor_ui

# 4. Start OS Sensor
cd member-3_os-multimodal-sensor && python -m os_sensor

# 5. Load Firefox Extension (about:debugging)
# 6. Launch VS Code with Extension
```

---

## 8. Git Workflow

### 8.1 Branch Strategy

```
main                        ← Production-ready, protected
├── develop                 ← Integration branch
├── member-1/feat-name      ← Member 1's feature branches
├── member-2/feat-name      ← Member 2's feature branches
├── member-3/feat-name      ← Member 3's feature branches
├── member-4/feat-name      ← Member 4's feature branches
├── member-5/feat-name      ← Member 5's feature branches
└── member-6/feat-name      ← Member 6's feature branches
```

### 8.2 Branch Naming Convention

```
member-{N}/{type}-{short-description}
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

Examples:
- `member-1/feat-youtube-detection`
- `member-4/fix-dedup-timing`
- `member-5/refactor-model-registry`

### 8.3 Commit Convention

```
[M{N}] type: short description

Optional longer description explaining why.
```

Examples:
- `[M1] feat: add YouTube watch-time tracking`
- `[M4] fix: resolve event deduplication race condition`
- `[M5] docs: update model benchmark results`

### 8.4 Pull Request Rules

1. All PRs target the `develop` branch
2. Require at least 1 review from another team member
3. PR title must follow commit convention
4. PR description must explain what and why
5. All tests must pass before merge
6. Use **squash merge** into `develop`
7. Use **merge commit** from `develop` into `main`

### 8.5 Conflict Resolution

- If a conflict is in **your own folder** → resolve it yourself
- If a conflict is in **another member's folder** → **DO NOT RESOLVE IT** → notify that member
- If a conflict is in **root files** (`contents.md`, `.gitignore`) → discuss with team

### 8.6 Protected Files

The following files require **team consensus** to modify:

- `contents.md` (root)
- `instructions.md` (root)
- `.gitignore` (root)
- `README.md` (root)

---

## 9. Security Rules

1. **Never commit secrets** — API keys, passwords, tokens, OAuth secrets
2. **Use `.env.example`** — Template files with empty values
3. **Real `.env` in `.gitignore`** — Always
4. **HTTPS for cloud APIs** — Never send API keys over HTTP
5. **Local shared secret** — For inter-service authentication (generated per-install)
6. **No telemetry** — Tesseract sends no usage data externally
7. **User data is sacred** — Observational data never leaves the device without explicit permission

---

## 10. Privacy Rules

1. **Local-first always** — Process data locally whenever possible
2. **No continuous screen streaming** — Capture structured events, not raw video
3. **PII stripping before cloud** — Remove file paths, usernames, code from cloud requests
4. **Context abstraction** — Send "struggling with C pointer dereferencing" not raw code
5. **User control** — Pause, stop, export, delete at any time
6. **Autonomy levels** — Consequential actions always require human approval
7. **Data retention** — Auto-purge according to configured retention periods
8. **Transparency** — User can view all collected data through the dashboard

---

## 11. Code Style & Standards

### Python (Members 3, 4, 5, 6)

- Formatter: **Black** (line length 100)
- Linter: **Ruff**
- Type checking: **mypy** (strict mode)
- Docstrings: Google style
- Imports: sorted with `isort`

### JavaScript/TypeScript (Members 1, 2, 6)

- Formatter: **Prettier**
- Linter: **ESLint**
- TypeScript: strict mode (Member 2, Member 6 frontend)

### General

- All functions must have docstrings/JSDoc
- All public interfaces must have type annotations
- All error paths must be handled explicitly
- Logging must use structured logging (not print statements)
