# Member 6 — Tutor & UI

> **Owner**: Member 6
> **Folder**: `member-6_tutor-ui/`
> **Status**: Phase 0 — Documentation

---

## 1. Component Responsibility

Member 6 owns the **user-facing layer** of Tesseract — everything the user sees and interacts with. This includes the progressive tutoring engine, recommendation system, automation engine, permission guard, and the system UI (tray app, dashboard, notifications).

---

## 2. Features

### 2.1 Progressive Assistance Engine (L1–L5)
- Orchestrate the escalating assistance levels based on friction scores
- L1: Generate a contextual hint (minimal)
- L2: Generate a concept explanation
- L3: Generate a detailed breakdown with examples
- L4: Generate a practice problem for the weak area
- L5: Provide a full solution (last resort)
- Respect the user's autonomy level settings

### 2.2 Roadmap Builder
- Build personalized learning roadmaps based on knowledge graph state
- Adapt roadmap based on available study time (30 min/day, 1 hr/day, etc.)
- Track progress through the roadmap
- Adjust based on new evidence (skip mastered topics, add weak ones)

### 2.3 Recommendation Engine
- Recommend learning resources based on current topic and knowledge gaps
- Group and deduplicate resources
- Rank by relevance, difficulty, and format preference
- Track which resources the user has already consumed

### 2.4 Automation Engine (Future)
- Detect repetitive workflow patterns
- Propose workflow automations for user approval
- Execute approved automations with permission guard
- Keep different users/documents distinct

### 2.5 Permission Guard (Autonomy Levels)
- Enforce the user's configured autonomy level (L0–L5)
- Block actions that exceed the current autonomy level
- Require explicit approval for consequential actions
- Log all actions and approvals for transparency

### 2.6 System Tray Application
- Background application with system tray icon
- Show Tesseract status (active, paused, processing)
- Quick access to pause/resume observation
- Quick access to dashboard
- Show notification count

### 2.7 Web Dashboard (Local)
- Main user interface served at `http://localhost:9702`
- Dashboard views:
  - **Overview**: Current context, active session, friction level
  - **Knowledge Graph**: Visual skill map with confidence levels
  - **Learning**: Active roadmap, progress, recommendations
  - **History**: Past episodes, sessions, activity timeline
  - **Settings**: Autonomy levels, privacy controls, model config
  - **Data**: View, export, delete collected data

### 2.8 Notification System
- Display non-intrusive notifications for:
  - Stuck detection (with progressive hint)
  - Milestone reached (skill improved)
  - Roadmap suggestions
  - Context changes
- Respect do-not-disturb and frequency settings

### 2.9 Approval Dialogs
- Modal dialogs for actions requiring explicit approval (L4–L5 autonomy)
- Show what action will be taken, its impact, and options to approve/deny

---

## 3. Internal Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Tutor & UI Service                           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Web Dashboard (port 9702)                    │  │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐│  │
│  │   │Overview   │  │Knowledge │  │Learning  │  │Settings││  │
│  │   │Page       │  │Graph View│  │Roadmap   │  │Page    ││  │
│  │   └──────────┘  └──────────┘  └──────────┘  └────────┘│  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                             │                                   │
│  ┌──────────────────────────┴───────────────────────────────┐  │
│  │              Backend API (Python)                         │  │
│  │                                                           │  │
│  │  ┌────────────────┐  ┌───────────────┐  ┌─────────────┐│  │
│  │  │Progressive     │  │Roadmap        │  │Recommendation││  │
│  │  │Assistance      │  │Builder        │  │Engine        ││  │
│  │  │Engine          │  │               │  │              ││  │
│  │  └────────────────┘  └───────────────┘  └─────────────┘│  │
│  │                                                           │  │
│  │  ┌────────────────┐  ┌───────────────┐  ┌─────────────┐│  │
│  │  │Automation      │  │Permission     │  │Notification  ││  │
│  │  │Engine          │  │Guard          │  │Manager       ││  │
│  │  └────────────────┘  └───────────────┘  └─────────────┘│  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           System Tray Application                        │  │
│  │   (Status icon, quick controls, notification badges)     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
         │                              │
         │ REST + WS                    │ REST
         ↓                              ↓
  Member 4 (Core Engine)         Member 5 (AI & Knowledge)
  Port 9700                      Port 9701
```

---

## 4. Inputs

| Input | Source | Protocol |
|:---|:---|:---|
| Current context / friction / episodes | Member 4 (Core Engine) | REST `http://localhost:9700/api/v1` |
| Real-time alerts (stuck, milestones) | Member 4 (Core Engine) | WebSocket `ws://localhost:9700/alerts` |
| Knowledge graph data | Member 5 (AI & Knowledge) | REST `http://localhost:9701/api/v1` |
| AI-generated hints/explanations/roadmaps | Member 5 (AI & Knowledge) | REST `http://localhost:9701/api/v1` |
| User interactions | Web Dashboard / System Tray | Local UI events |

---

## 5. Outputs

### 5.1 User-Facing Outputs

| Output | Delivery |
|:---|:---|
| Progressive hints (L1–L5) | Dashboard notification + popup |
| Knowledge graph visualization | Dashboard page |
| Learning roadmap | Dashboard page |
| Resource recommendations | Dashboard page |
| Friction alerts | System notification |
| Milestone celebrations | System notification |
| Approval dialogs | Dashboard modal |
| Settings changes | REST calls to Members 4, 5 |

### 5.2 No Outbound APIs

Member 6 does **not** expose APIs that other members consume. It is a pure consumer of Members 4 and 5.

---

## 6. Data Structures

### 6.1 Assistance Notification

```json
{
  "notification_id": "uuid-v4",
  "type": "stuck_assistance",
  "level": 2,
  "title": "Struggling with Pointer Dereferencing?",
  "content": "A pointer stores a memory address. The * operator accesses the value at that address...",
  "topic": "c-pointers-dereferencing",
  "friction_score": 0.73,
  "actions": [
    { "label": "Show More Detail", "action": "escalate_to_L3" },
    { "label": "Dismiss", "action": "dismiss" },
    { "label": "Don't show for this topic", "action": "mute_topic" }
  ],
  "timestamp": "ISO-8601"
}
```

### 6.2 Roadmap

```json
{
  "roadmap_id": "uuid-v4",
  "subject": "C Programming",
  "current_level": "beginner",
  "available_time": "1_hour_per_day",
  "milestones": [
    {
      "topic": "Variables & Data Types",
      "status": "completed",
      "confidence": 0.92,
      "estimated_hours": 3
    },
    {
      "topic": "Pointers",
      "status": "in_progress",
      "confidence": 0.30,
      "estimated_hours": 8,
      "subtopics": [
        { "topic": "Dereferencing", "status": "struggling", "confidence": 0.25 },
        { "topic": "NULL handling", "status": "developing", "confidence": 0.45 }
      ]
    }
  ],
  "estimated_completion": "2026-10-15"
}
```

---

## 7. Dependencies

### Internal Dependencies (at runtime)

| Dependency | Member | Interface |
|:---|:---|:---|
| Core Engine (data + alerts) | Member 4 | REST `http://localhost:9700/api/v1` + WS `ws://localhost:9700/alerts` |
| AI & Knowledge (inference + KG + tutor) | Member 5 | REST `http://localhost:9701/api/v1` |

### External Dependencies

| Package | Purpose |
|:---|:---|
| `aiohttp` | Async HTTP server (dashboard backend) |
| `httpx` | Async HTTP client (calls to Members 4, 5) |
| `websockets` | WebSocket client (alerts from Member 4) |
| `jinja2` | HTML template rendering |
| `pystray` | System tray icon (cross-platform) |
| `Pillow` | Tray icon image |
| `python-dotenv` | Environment config |

### Frontend Dependencies (dashboard)

| Technology | Purpose |
|:---|:---|
| HTML5 + CSS3 + Vanilla JS | Dashboard UI |
| D3.js or vis.js | Knowledge graph visualization |
| Chart.js | Analytics charts |

---

## 8. Interfaces

### 8.1 Inbound: Core Engine Data (REST Client)

- **Interface Name**: `CoreDataAPI`
- **Owner**: Member 4 (server)
- **Consumer**: Member 6 (this component — client)
- **Base URL**: `http://localhost:9700/api/v1`

### 8.2 Inbound: Core Engine Alerts (WebSocket Client)

- **Interface Name**: `CoreEventStream`
- **Owner**: Member 4 (server)
- **Consumer**: Member 6 (this component — client)
- **Endpoint**: `ws://localhost:9700/alerts`

### 8.3 Inbound: AI & Knowledge (REST Client)

- **Interface Name**: `AIInferenceAPI` + `TutorAIAPI`
- **Owner**: Member 5 (server)
- **Consumer**: Member 6 (this component — client)
- **Base URL**: `http://localhost:9701/api/v1`

---

## 9. Testing

### Unit Tests
- Progressive assistance engine escalates correctly (L1 → L2 → ... → L5)
- Permission guard blocks actions exceeding autonomy level
- Notification manager respects frequency limits
- Roadmap builder adapts to available time
- Recommendation engine deduplicates resources

### UI Tests
- Dashboard pages render correctly
- Knowledge graph visualization displays nodes and edges
- Notifications appear and can be dismissed
- Settings page saves and applies changes

### Integration Tests (Phase 2+)
- Dashboard displays real data from Member 4
- Alerts from Member 4 trigger notifications
- Tutor requests to Member 5 return and display correctly
- Knowledge graph visualization reflects real KG data

---

## 10. Definition of Done

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

---

## 11. What This Member Owns

- Progressive assistance engine (L1–L5 orchestration)
- Roadmap builder and progress tracking
- Recommendation engine
- Automation engine (workflow detection + replay)
- Permission guard (autonomy level enforcement)
- System tray application
- Web dashboard (all pages, frontend + backend)
- Notification system
- Approval dialog system
- User settings management
- Data export / deletion UI

---

## 12. What This Member Does NOT Own

- Event collection (Members 1, 2, 3)
- Event aggregation / normalization (Member 4)
- Session / episode building (Member 4)
- Stuck detection / friction scoring (Member 4)
- AI model management / inference (Member 5)
- Knowledge graph data model / CRUD (Member 5)
- Embedding pipeline (Member 5)
- OCR processing (Member 3)
