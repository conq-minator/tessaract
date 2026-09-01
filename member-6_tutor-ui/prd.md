# Member 6 — Tutor & UI: Product Requirements Document

> **Owner**: Member 6  
> **Version**: 0.1.0  
> **Status**: Phase 0 — Documentation  
> **Last Updated**: 2026-09-01

---

## 1. Executive Summary

Member 6 is the **user-facing layer** of Tesseract. It owns everything the end user sees and interacts with — the progressive tutoring engine, learning roadmap builder, recommendation system, permission guard, notification system, system tray application, and the local web dashboard.

This component is a **pure consumer**. It does not expose APIs for other members. It reads data from Member 4 (Core Engine) and Member 5 (AI & Knowledge) and presents it to the user through a polished, responsive interface.

---

## 2. User Personas

### 2.1 Primary — The Learner
- A student or self-taught programmer learning a subject (e.g., C programming)
- Uses VS Code, Firefox, and a terminal daily
- Wants to know where they're weak, what to study next, and get help when stuck
- Values autonomy — prefers hints over answers

### 2.2 Secondary — The Power User
- A developer or knowledge worker who wants workflow insights
- Interested in the knowledge graph, session history, and analytics
- Wants fine-grained control over autonomy levels and privacy settings

---

## 3. Feature Requirements (MoSCoW)

### 3.1 Must Have (P0)

| ID | Feature | Description |
|:---|:---|:---|
| F-01 | Web Dashboard | Local web UI at `http://localhost:9702` with 6 pages |
| F-02 | Overview Page | Current context, active session, friction level display |
| F-03 | Knowledge Graph Page | Visual skill map with confidence-colored nodes |
| F-04 | Learning Page | Active roadmap, progress tracking, resource recommendations |
| F-05 | Settings Page | Autonomy level config, privacy controls, theme selection |
| F-06 | Data Page | View, export, and delete collected data |
| F-07 | Progressive Assistance Engine | L1–L5 escalating assistance based on friction scores |
| F-08 | Permission Guard | Enforce autonomy levels (L0–L5), block exceeding actions |
| F-09 | Notification System | Non-intrusive alerts for stuck detection, milestones, suggestions |
| F-10 | Mock Data Mode | Full UI development without Members 4 or 5 running |

### 3.2 Should Have (P1)

| ID | Feature | Description |
|:---|:---|:---|
| F-11 | History Page | Past episodes, sessions, activity timeline |
| F-12 | Roadmap Builder | Personalized learning roadmaps based on knowledge graph |
| F-13 | Recommendation Engine | Ranked learning resources by relevance and difficulty |
| F-14 | System Tray App | Background app with status icon, quick controls, badge count |
| F-15 | Approval Dialogs | Modal dialogs for L4–L5 autonomy actions requiring consent |
| F-16 | WebSocket Alert Listener | Real-time alerts from Member 4 (stuck, milestones) |

### 3.3 Could Have (P2)

| ID | Feature | Description |
|:---|:---|:---|
| F-17 | Automation Engine | Detect repetitive workflows, propose automations |
| F-18 | Do-Not-Disturb Mode | Suppress notifications during focus sessions |
| F-19 | Notification Frequency Limits | Configurable cooldown between notifications |
| F-20 | Resource Consumption Tracking | Track which learning resources the user has already used |

### 3.4 Won't Have (This Version)

| ID | Feature | Reason |
|:---|:---|:---|
| F-21 | Mobile UI | Desktop-first, mobile planned post-MVP |
| F-22 | Multi-user support | Single-user local application |
| F-23 | Cloud dashboard | All data and UI remain local |

---

## 4. Functional Requirements

### 4.1 Progressive Assistance Engine (L1–L5)

| Requirement | Description |
|:---|:---|
| PAE-01 | Accept friction score and current topic from Member 4 |
| PAE-02 | Map friction score to assistance level (L1–L5) |
| PAE-03 | Request appropriate content from Member 5's tutor API |
| PAE-04 | L1: Contextual hint (minimal nudge) |
| PAE-05 | L2: Concept explanation (teach the principle) |
| PAE-06 | L3: Detailed breakdown with examples |
| PAE-07 | L4: Practice problem for the weak area |
| PAE-08 | L5: Full solution (last resort only) |
| PAE-09 | Respect user's autonomy level — never exceed configured max |
| PAE-10 | Allow user to manually escalate (e.g., "Show More Detail") |
| PAE-11 | Allow user to dismiss or mute notifications per topic |

### 4.2 Roadmap Builder

| Requirement | Description |
|:---|:---|
| RB-01 | Fetch knowledge graph state from Member 5 |
| RB-02 | Request roadmap generation from Member 5's `/tutor/roadmap` |
| RB-03 | Display milestones with status, confidence, and estimated hours |
| RB-04 | Support time-based adaptation (30 min/day, 1 hr/day, etc.) |
| RB-05 | Track progress through the roadmap |
| RB-06 | Adjust roadmap when new evidence arrives (skip mastered, add weak) |

### 4.3 Recommendation Engine

| Requirement | Description |
|:---|:---|
| RE-01 | Fetch recommendations from Member 5's `/tutor/recommend` |
| RE-02 | Display resources grouped and ranked by relevance |
| RE-03 | Show difficulty level and format (video, article, exercise) |
| RE-04 | Deduplicate resources |
| RE-05 | Track consumed resources |

### 4.4 Permission Guard

| Requirement | Description |
|:---|:---|
| PG-01 | Read user's configured autonomy level (L0–L5) from settings |
| PG-02 | Before any action, check if it exceeds the current level |
| PG-03 | Block actions that exceed the level with a clear message |
| PG-04 | For L4 actions, show approval dialog before executing |
| PG-05 | Log all actions and approval/denial decisions |
| PG-06 | Consequential actions always require explicit approval regardless of level |

### 4.5 Notification System

| Requirement | Description |
|:---|:---|
| NS-01 | Display non-intrusive toast notifications in the dashboard |
| NS-02 | Notification types: stuck_assistance, milestone, roadmap_suggestion, context_change |
| NS-03 | Each notification includes title, content, topic, actions (escalate, dismiss, mute) |
| NS-04 | Respect notification cooldown setting (`TESSERACT_NOTIFICATION_COOLDOWN_S`) |
| NS-05 | Respect do-not-disturb mode |
| NS-06 | Show notification count badge in system tray |

### 4.6 Web Dashboard

| Requirement | Description |
|:---|:---|
| WD-01 | Serve at `http://localhost:9702` via aiohttp |
| WD-02 | 6 pages: Overview, Knowledge Graph, Learning, History, Settings, Data |
| WD-03 | Dark theme by default, configurable |
| WD-04 | Responsive layout (desktop-first, tablet-friendly) |
| WD-05 | Real-time updates via WebSocket or polling |
| WD-06 | Accessible (WCAG 2.1 AA baseline) |

### 4.7 System Tray Application

| Requirement | Description |
|:---|:---|
| ST-01 | Background process with system tray icon (pystray) |
| ST-02 | Show Tesseract status: active, paused, processing |
| ST-03 | Quick actions: pause/resume observation, open dashboard |
| ST-04 | Show notification count badge |
| ST-05 | Graceful startup and shutdown |

---

## 5. Non-Functional Requirements

| Category | Requirement |
|:---|:---|
| **Performance** | Dashboard pages must load in under 500ms on localhost |
| **Performance** | Knowledge graph must render up to 200 nodes smoothly |
| **Performance** | Notifications must appear within 1s of alert receipt |
| **Memory** | Dashboard backend must use < 100 MB RAM at idle |
| **Responsiveness** | UI must be usable on screens 1024px+ wide |
| **Accessibility** | WCAG 2.1 AA compliance (color contrast, keyboard nav, ARIA labels) |
| **Reliability** | Graceful degradation if Members 4 or 5 are unavailable |
| **Security** | No secrets in code; shared-secret auth for upstream calls |
| **Privacy** | No telemetry; all data stays local |

---

## 6. Acceptance Criteria (Definition of Done)

- [ ] System tray application runs in the background
- [ ] Web dashboard is accessible at `http://localhost:9702`
- [ ] Overview page shows current context and friction level
- [ ] Knowledge graph visualization renders skill nodes with confidence colors
- [ ] Progressive assistance works from L1 to L5
- [ ] Notifications appear for stuck detection and milestones
- [ ] Settings page allows configuring autonomy levels
- [ ] Data page allows viewing and deleting collected data
- [ ] Permission guard enforces autonomy levels
- [ ] All unit tests pass
- [ ] UI is responsive and accessible
- [ ] Mock data mode works without Members 4 or 5

---

## 7. API Contracts Consumed

### 7.1 From Member 4 — Core Engine (Port 9700)

| Method | Endpoint | Purpose |
|:---|:---|:---|
| GET | `/api/v1/context/current` | Current user context |
| GET | `/api/v1/friction/current` | Current friction score |
| GET | `/api/v1/episodes/recent` | Recent learning episodes |
| GET | `/api/v1/sessions/active` | Active session info |
| GET | `/api/v1/analytics/summary` | Analytics data |
| WS | `ws://localhost:9700/alerts` | Real-time alerts (stuck, milestones) |

### 7.2 From Member 5 — AI & Knowledge (Port 9701)

| Method | Endpoint | Purpose |
|:---|:---|:---|
| GET | `/api/v1/knowledge/graph` | Full knowledge graph |
| GET | `/api/v1/knowledge/gaps` | Knowledge gaps |
| POST | `/api/v1/tutor/hint` | Generate hint (L1) |
| POST | `/api/v1/tutor/explain` | Generate explanation (L2–L3) |
| POST | `/api/v1/tutor/practice` | Generate practice problem (L4) |
| POST | `/api/v1/tutor/roadmap` | Generate/update roadmap |
| POST | `/api/v1/tutor/recommend` | Get resource recommendations |

---

## 8. Out of Scope

- Event collection (Members 1, 2, 3)
- Event aggregation / normalization (Member 4)
- Session / episode building (Member 4)
- Stuck detection / friction scoring (Member 4)
- AI model management / inference (Member 5)
- Knowledge graph data model / CRUD (Member 5)
- Embedding pipeline (Member 5)
- OCR processing (Member 3)
