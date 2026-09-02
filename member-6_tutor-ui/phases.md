# Member 6 — Tutor & UI: Development Phases

> **Owner**: Member 6  
> **Version**: 0.1.0  
> **Last Updated**: 2026-09-01

---

## Overview

The entire Member 6 workload is divided into **4 phases**, each building on the previous one. Each phase produces a testable, working increment.

```
Phase 1: Foundation & Mock Backend
        │
        ▼
Phase 2: Dashboard Core UI
        │
        ▼
Phase 3: Engine Integration
        │
        ▼
Phase 4: System Tray, Polish & Testing
```

---

## Phase 1 — Foundation & Mock Backend

> **Goal**: A running aiohttp server with mock data, basic routing, and project scaffolding.  
> **Deliverable**: `python -m tutor_ui --mock-data --no-tray` starts a server at `localhost:9702` that serves a health endpoint and returns mock JSON data.

### Tasks

| # | Task | Files Created/Modified |
|:---|:---|:---|
| 1.1 | Create `pyproject.toml` with all dependencies and `[project.scripts]` | `pyproject.toml` |
| 1.2 | Create package structure: `src/tutor_ui/__init__.py`, `__main__.py` | `src/tutor_ui/` |
| 1.3 | Implement `config.py` — load `.env`, create `TesseractUIConfig` dataclass | `src/tutor_ui/config.py` |
| 1.4 | Implement `app.py` — aiohttp application factory, static files, templates | `src/tutor_ui/app.py` |
| 1.5 | Implement `routes/health.py` — `GET /health` returning service status | `src/tutor_ui/routes/health.py` |
| 1.6 | Implement `routes/dashboard.py` — stub routes for all 6 pages | `src/tutor_ui/routes/dashboard.py` |
| 1.7 | Implement `routes/api.py` — internal API routes returning mock JSON | `src/tutor_ui/routes/api.py` |
| 1.8 | Implement `models/` — dataclasses for Notification, Roadmap, Context, Settings | `src/tutor_ui/models/` |
| 1.9 | Implement `mock/mock_core.py` — synthetic data for Member 4 responses | `src/tutor_ui/mock/mock_core.py` |
| 1.10 | Implement `mock/mock_ai.py` — synthetic data for Member 5 responses | `src/tutor_ui/mock/mock_ai.py` |
| 1.11 | Implement `utils/logging.py` — structured logging configuration | `src/tutor_ui/utils/logging.py` |
| 1.12 | Create `templates/base.html` — base template with CDN links (D3, Chart.js, Inter font) | `templates/base.html` |
| 1.13 | Create initial `static/css/main.css` — CSS variables, reset, dark theme | `static/css/main.css` |
| 1.14 | Write basic tests: config loading, health endpoint, mock data | `tests/` |

### Exit Criteria

- [x] `python -m tutor_ui --mock-data --no-tray` starts without errors
- [x] `GET http://localhost:9702/health` returns `200 OK`
- [x] `GET http://localhost:9702/api/context` returns mock JSON
- [x] All stub page routes return 200
- [x] `pytest` passes with all Phase 1 tests
- [x] Logging output is structured (no `print()`)

---

## Phase 2: Dashboard Core UI
**Status**: [x] Completed

**Goal**: Build out the local web interface that visualizes data from Members 4 & 5.mock backend API.  
> **Deliverable**: A fully navigable, visually polished dashboard at `localhost:9702` with dark theme, responsive layout, and all pages populated with mock data.

### Tasks

| # | Task | Files Created/Modified |
|:---|:---|:---|
| 2.1 | Build navigation sidebar component | `templates/components/sidebar.html`, `static/js/components/navigation.js`, `static/css/components.css` |
| 2.2 | Build **Overview** page — context card, friction meter, session info | `templates/pages/overview.html`, `static/js/pages/overview.js` |
| 2.3 | Build **Knowledge Graph** page — D3.js force-directed graph | `templates/pages/knowledge_graph.html`, `static/js/pages/knowledge-graph.js`, `static/css/knowledge-graph.css` |
| 2.4 | Build **Learning** page — roadmap timeline, recommendations, progress | `templates/pages/learning.html`, `static/js/pages/learning.js` |
| 2.5 | Build **History** page — episode list, session timeline | `templates/pages/history.html`, `static/js/pages/history.js` |
| 2.6 | Build **Settings** page — autonomy levels, privacy controls, theme | `templates/pages/settings.html`, `static/js/pages/settings.js` |
| 2.7 | Build **Data** page — data browser, export button, delete controls | `templates/pages/data.html`, `static/js/pages/data.js` |
| 2.8 | Implement `static/js/api.js` — fetch wrapper for all dashboard API calls | `static/js/api.js` |
| 2.9 | Implement `static/js/app.js` — page router, global state, init | `static/js/app.js` |
| 2.10 | Build notification toast component | `templates/components/notification.html`, `static/js/components/notification.js`, `static/css/notifications.css` |
| 2.11 | Build modal/dialog component | `templates/components/modal.html`, `static/js/components/modal.js` |
| 2.12 | Build Chart.js wrapper for analytics | `static/js/components/charts.js` |
| 2.13 | Finalize responsive layout and dark theme | `static/css/dashboard.css`, `static/css/main.css` |
| 2.14 | Create SVG icon set for dashboard | `static/assets/icons/` |
| 2.15 | Write route tests for all pages | `tests/test_routes.py` |

### Exit Criteria

- [x] Overview page shows current context and session stats
- [x] Knowledge Graph renders interactive nodes via D3.js
- [x] Learning page shows roadmap timeline and recommendations
- [x] History page shows past episodes in a table
- [x] Settings page contains Autonomy Level selectors
- [x] Navigation sidebar works across all pages
- [x] UI handles "mock mode" vs "live mode" gracefully (via API error handling)
- [ ] Notification toast appears and dismisses
- [ ] No JS console errors

---

## Phase 3: Engine Integration
**Status**: [x] Completed

> **Goal**: Backend services are fully implemented. Dashboard talks to real Members 4 & 5 (or mocks that faithfully replicate their APIs).  
> **Deliverable**: Progressive assistance, roadmap building, recommendations, and permission guard all work end-to-end through the dashboard.

### Tasks

| # | Task | Files Created/Modified |
|:---|:---|:---|
| 3.1 | Implement `clients/core_client.py` — real HTTP client for Member 4 | `src/tutor_ui/clients/core_client.py` |
| 3.2 | Implement `clients/ai_client.py` — real HTTP client for Member 5 | `src/tutor_ui/clients/ai_client.py` |
| 3.3 | Implement `clients/alert_listener.py` — WebSocket client for Member 4 alerts | `src/tutor_ui/clients/alert_listener.py` |
| 3.4 | Implement `utils/auth.py` — shared-secret auth header injection | `src/tutor_ui/utils/auth.py` |
| 3.5 | Implement `services/assistance.py` — Progressive Assistance Engine (L1–L5) | `src/tutor_ui/services/assistance.py` |
| 3.6 | Implement `services/roadmap.py` — Roadmap Builder | `src/tutor_ui/services/roadmap.py` |
| 3.7 | Implement `services/recommendation.py` — Recommendation Engine | `src/tutor_ui/services/recommendation.py` |
| 3.8 | Implement `services/permission.py` — Permission Guard | `src/tutor_ui/services/permission.py` |
| 3.9 | Implement `services/notification.py` — Notification Manager (cooldowns, DND) | `src/tutor_ui/services/notification.py` |
| 3.10 | Wire real services into `routes/api.py` (replace mock responses) | `src/tutor_ui/routes/api.py` |
| 3.11 | Wire alert listener into app startup/shutdown | `src/tutor_ui/app.py` |
| 3.12 | Add real-time notification push to browser (SSE or WebSocket) | `src/tutor_ui/routes/api.py`, `static/js/app.js` |
| 3.13 | Implement `--mock-data` flag to swap between real and mock clients | `src/tutor_ui/__main__.py`, `src/tutor_ui/app.py` |
| 3.14 | Write unit tests for all services | `tests/test_assistance.py`, `tests/test_permission.py`, etc. |
| 3.15 | Write client tests (mocked HTTP) | `tests/test_clients.py` |

### Exit Criteria

- [x] Progressive assistance escalates correctly L1 → L2 → ... → L5
- [x] Permission guard blocks actions exceeding autonomy level
- [x] Notification manager respects cooldown settings
- [x] Roadmap builder fetches and displays real roadmap data
- [x] Recommendation engine returns ranked resources
- [x] Alert listener connects to Member 4's WebSocket
- [x] `--mock-data` flag correctly swaps between real and mock clients
- [x] All service unit tests pass
- [x] All client tests pass (with mocked HTTP)

---

## Phase 4: System Tray, Polish & Testing
**Status**: [x] Completed

> **Goal**: System tray app works, approval dialogs are functional, full test coverage, and production-ready polish.  
> **Deliverable**: `python -m tutor_ui` starts both the dashboard and system tray. Everything works end-to-end.

### Tasks

| # | Task | Files Created/Modified |
|:---|:---|:---|
| 4.1 | Implement `tray/tray_app.py` — pystray system tray with status/controls | `src/tutor_ui/tray/tray_app.py` |
| 4.2 | Create tray icon assets (active, paused, processing) | `src/tutor_ui/tray/icons/` |
| 4.3 | Wire tray app into `__main__.py` (start alongside dashboard) | `src/tutor_ui/__main__.py` |
| 4.4 | Implement approval dialog flow (frontend modal + backend permission check) | `static/js/components/modal.js`, `src/tutor_ui/services/permission.py` |
| 4.5 | Implement `services/automation.py` — stub for workflow detection (future) | `src/tutor_ui/services/automation.py` |
| 4.6 | Add notification badge count to tray icon | `src/tutor_ui/tray/tray_app.py` |
| 4.7 | Add loading and error states to all pages | `static/js/pages/*.js`, `static/css/components.css` |
| 4.8 | Add keyboard navigation support (tab, enter, escape) | `static/js/app.js`, `templates/` |
| 4.9 | Add ARIA labels to all interactive elements | `templates/` |
| 4.10 | Performance audit — ensure pages load < 500ms | All |
| 4.11 | Write remaining unit tests (>80% coverage on services/) | `tests/` |
| 4.12 | Write API route tests | `tests/test_api.py` |
| 4.13 | Manual test all pages with mock data | — |
| 4.14 | Update documentation (architecture, memory) with final state | `architecture.md`, `memory.md` |

### Exit Criteria

- [x] System tray icon appears and shows correct status
- [x] Tray menu: pause/resume, open dashboard, quit
- [x] Approval dialogs appear for L4–L5 actions
- [x] All pages have loading and error states
- [x] Keyboard navigation works for all interactive elements
- [x] ARIA labels present on all interactive elements
- [x] `pytest` passes with >80% coverage on `services/`
- [x] All pages load in < 500ms (localhost)
- [x] `python -m tutor_ui` starts both dashboard and tray cleanly
- [x] `python -m tutor_ui --mock-data` works without Members 4 or 5
- [x] No console errors, no unhandled exceptions

---

## Phase Summary

| Phase | Name | Key Focus | Key Output |
|:---|:---|:---|:---|
| **1** | Foundation & Mock Backend | Scaffolding, config, mocks, server skeleton | Running server + mock API |
| **2** | Dashboard Core UI | All 6 pages, dark theme, responsive, KG visualization | Navigable UI with mock data |
| **3** | Engine Integration | Assistance, roadmap, recommendations, permissions, alerts | Working backend services |
| **4** | System Tray, Polish & Testing | Tray app, dialogs, accessibility, tests, performance | Production-ready system |

---

## Dependency Order

```
Phase 1 is independent (no external dependencies)
Phase 2 depends on Phase 1 (routes, templates, mock API)
Phase 3 depends on Phase 2 (pages exist) + Phase 1 (mock infrastructure)
Phase 4 depends on Phase 3 (services exist) + Phase 2 (UI exists)
```

> **Note**: During Phase 1–3, use `--mock-data` mode exclusively. Real integration with Members 4 and 5 happens during the project-wide Phase 2 (Interface Testing) per the master project plan.
