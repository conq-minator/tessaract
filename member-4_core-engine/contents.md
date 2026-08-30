# Member 4 — Core Engine

> **Owner**: Member 4
> **Folder**: `member-4_core-engine/`
> **Status**: Phase 0 — Documentation

---

## 1. Component Responsibility

Member 4 owns the **Core Engine** — the central nervous system of Tesseract. It receives events from all sensors, normalizes and stores them, builds context and sessions, detects behavioral patterns, and provides data to downstream consumers (AI layer, UI).

This is the **deterministic backbone** of Tesseract. It uses **rule-based, statistical, and event-driven processing** — not LLMs — for the majority of its work. AI is called only when rule-based methods are insufficient.

---

## 2. Features

### 2.1 WebSocket Event Server
- Accept WebSocket connections from all sensors (Members 1, 2, 3)
- Authenticate connections using shared secret
- Receive TesseractEvent JSON messages
- Handle multiple simultaneous sensor connections

### 2.2 Event Normalization & Deduplication
- Normalize events from different sources into a uniform internal format
- Deduplicate events (e.g., rapid file saves, duplicate tab activations)
- Apply rate limiting to prevent event flooding

### 2.3 Event Store
- Persist all events to SQLite (append-only event log)
- Support querying by source, type, time range
- Implement data retention policies (auto-purge after configurable days)

### 2.4 Session Builder
- Group events into user sessions (continuous periods of activity)
- Detect session start and end based on idle timeouts
- Track session duration and activity composition

### 2.5 Episode Grouper
- Group related events across sessions into **learning episodes**
- An episode represents a coherent learning/work unit:
  ```
  VS Code → C program → error → fix → re-run → Google search →
  YouTube tutorial → retry → success = ONE EPISODE
  ```
- Use heuristics: time proximity, topic similarity, source correlation

### 2.6 Intent Classifier (Rule-Based)
- Classify current user activity into categories:
  - Learning (watching tutorials, reading docs, trying code)
  - Working (productive coding, writing)
  - Debugging (error cycles, searching for solutions)
  - Exploring (browsing, reading)
  - Idle
- Use deterministic rules first; request AI classification only for ambiguous cases

### 2.7 Stuck Detector
- Calculate a **friction score** based on behavioral signals:
  - Same error repeated (×weight)
  - Number of execution attempts (×weight)
  - Related searches performed (×weight)
  - Time spent without progress (×weight)
  - Tutorials opened (×weight)
- Detect when friction score exceeds thresholds
- Emit `stuck_detected` alerts with severity levels

### 2.8 Friction Scorer
- Maintain running friction scores per topic/session
- Decay scores over time (friction resolves naturally)
- Use configurable weights for each signal type

### 2.9 Behavioral Analysis Engine
- Aggregate patterns across episodes:
  - Repeated errors on the same concept
  - Time-to-resolution trends
  - Search patterns indicating confusion
  - Resource consumption patterns
- Provide behavioral summaries for the Knowledge Graph (Member 5)

### 2.10 REST API
- Serve data to downstream consumers (Member 6 — Tutor/UI)
- Provide current context, recent events, sessions, episodes, friction scores

### 2.11 WebSocket Alert Stream
- Push real-time alerts to the UI (Member 6):
  - `stuck_detected`
  - `episode_completed`
  - `context_changed`
  - `milestone_reached`

---

## 3. Internal Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Core Engine                               │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │           WebSocket Event Server (port 9700)           │  │
│  │   Accepts connections from Members 1, 2, 3             │  │
│  └──────────────────────┬─────────────────────────────────┘  │
│                         ↓                                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │         Event Normalizer & Deduplicator                │  │
│  └──────────────────────┬─────────────────────────────────┘  │
│                         ↓                                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Event Store (SQLite)                      │  │
│  └──────────────────────┬─────────────────────────────────┘  │
│                         ↓                                     │
│  ┌─────────────┐  ┌────────────┐  ┌────────────────────┐   │
│  │Session      │  │Episode     │  │Intent Classifier   │   │
│  │Builder      │  │Grouper     │  │(Rule-based)        │   │
│  └──────┬──────┘  └─────┬──────┘  └─────────┬──────────┘   │
│         │               │                    │               │
│         ↓               ↓                    ↓               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │        Behavioral Analysis Engine                      │  │
│  │   ┌──────────────┐  ┌──────────────────┐              │  │
│  │   │Stuck Detector│  │Friction Scorer   │              │  │
│  │   └──────────────┘  └──────────────────┘              │  │
│  └──────────────────────┬─────────────────────────────────┘  │
│                         │                                     │
│         ┌───────────────┼───────────────────┐                │
│         ↓               ↓                   ↓                │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐      │
│  │REST API  │  │WS Alert      │  │AI Request        │      │
│  │(port 9700│  │Stream        │  │(→ Member 5)      │      │
│  │/api/v1)  │  │(port 9700    │  │                  │      │
│  │          │  │/alerts)      │  │                  │      │
│  └──────────┘  └──────────────┘  └──────────────────┘      │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Inputs

| Input | Source | Protocol |
|:---|:---|:---|
| Browser events | Member 1 | WebSocket (client → server) |
| VS Code events | Member 2 | WebSocket (client → server) |
| OS/multimodal events | Member 3 | WebSocket (client → server) |

---

## 5. Outputs

### 5.1 REST API (consumed by Member 6)

| Method | Path | Response |
|:---|:---|:---|
| GET | `/api/v1/events/recent` | Recent structured events |
| GET | `/api/v1/sessions/active` | Current active session |
| GET | `/api/v1/sessions/{id}` | Session details with episodes and events |
| GET | `/api/v1/episodes/recent` | Recent learning episodes |
| GET | `/api/v1/friction/current` | Current friction/stuck score |
| GET | `/api/v1/context/current` | Current user context (topic, activity, tools) |
| GET | `/api/v1/analytics/summary` | Daily/weekly analytics summary |

### 5.2 WebSocket Alerts (consumed by Member 6)

| Alert Type | Payload |
|:---|:---|
| `stuck_detected` | `{friction_score, episode_id, topic, level}` |
| `episode_completed` | `{episode_id, summary, outcome}` |
| `context_changed` | `{new_context, old_context}` |
| `milestone_reached` | `{skill, old_confidence, new_confidence}` |

### 5.3 AI Requests (consumed by Member 5)

When rule-based methods are insufficient, the Core Engine makes REST calls to Member 5:

| Purpose | Endpoint |
|:---|:---|
| Classify ambiguous intent | `POST /api/v1/inference/classify` |
| Summarize episode | `POST /api/v1/inference/complete` |
| Update knowledge graph | `POST /api/v1/knowledge/update` |

---

## 6. Data Structures

### 6.1 Internal Session

```json
{
  "session_id": "uuid-v4",
  "start_time": "ISO-8601",
  "end_time": "ISO-8601 | null",
  "is_active": true,
  "events_count": 142,
  "sources": ["browser", "vscode"],
  "primary_intent": "debugging",
  "topics": ["c-programming", "pointers"]
}
```

### 6.2 Internal Episode

```json
{
  "episode_id": "uuid-v4",
  "session_ids": ["uuid-v4"],
  "start_time": "ISO-8601",
  "end_time": "ISO-8601 | null",
  "topic": "c-pointers-dereferencing",
  "intent": "learning",
  "outcome": "resolved | ongoing | abandoned",
  "events_count": 23,
  "friction_score": 0.73,
  "signals": {
    "error_count": 4,
    "execution_attempts": 7,
    "search_count": 3,
    "time_spent_s": 1260,
    "tutorials_opened": 1
  }
}
```

### 6.3 Friction Score

```json
{
  "score": 0.73,
  "level": "high",
  "signals": {
    "repeated_errors": { "count": 4, "weight": 0.3, "contribution": 0.22 },
    "execution_attempts": { "count": 7, "weight": 0.2, "contribution": 0.14 },
    "search_count": { "count": 3, "weight": 0.15, "contribution": 0.11 },
    "time_without_progress_s": { "value": 1260, "weight": 0.25, "contribution": 0.18 },
    "tutorials_opened": { "count": 1, "weight": 0.1, "contribution": 0.08 }
  },
  "threshold_low": 0.3,
  "threshold_medium": 0.5,
  "threshold_high": 0.7
}
```

---

## 7. Dependencies

### Internal Dependencies (at runtime)

| Dependency | Member | Interface | Required |
|:---|:---|:---|:---|
| AI Inference API | Member 5 | REST `http://localhost:9701/api/v1` | Optional (for ambiguous classification) |

### External Dependencies

| Package | Purpose |
|:---|:---|
| `aiohttp` | Async HTTP server (REST API) |
| `websockets` | WebSocket server |
| `sqlite3` (stdlib) | Event store |
| `asyncio` (stdlib) | Async event loop |
| `python-dotenv` | Environment config |

---

## 8. Interfaces

### 8.1 Inbound: Sensors → Core Engine (WebSocket Server)

- **Interface Name**: `SensorEventStream`
- **Owner**: Member 4 (this component — server)
- **Consumers**: Members 1, 2, 3 (clients)
- **Protocol**: WebSocket
- **Endpoint**: `ws://localhost:9700/events`
- **Auth**: `Authorization: Bearer <TESSERACT_SHARED_SECRET>` in handshake

### 8.2 Outbound: Core Engine → AI Layer (REST Client)

- **Interface Name**: `AIInferenceAPI`
- **Owner**: Member 5 (server)
- **Consumer**: Member 4 (this component — client)
- **Protocol**: REST
- **Base URL**: `http://localhost:9701/api/v1`

### 8.3 Outbound: Core Engine → Tutor/UI (REST + WebSocket Server)

- **Interface Name**: `CoreDataAPI` + `CoreEventStream`
- **Owner**: Member 4 (this component — server)
- **Consumer**: Member 6 (client)
- **REST**: `http://localhost:9700/api/v1`
- **WebSocket**: `ws://localhost:9700/alerts`

---

## 9. Testing

### Unit Tests
- Event normalizer correctly handles events from all three sources
- Deduplicator removes duplicate events within time window
- Session builder correctly detects session boundaries
- Episode grouper correlates related events
- Stuck detector calculates correct friction scores
- Friction scorer decays scores over time
- Intent classifier correctly categorizes known patterns
- REST API returns correct responses

### Integration Tests (Phase 2+)
- Accept real events from Members 1, 2, 3
- Full pipeline: event → store → session → episode → friction
- REST API serves correct data to Member 6
- WebSocket alerts fire at correct thresholds

---

## 10. Definition of Done

- [ ] WebSocket server accepts connections from all three sensors
- [ ] Events are normalized and stored in SQLite
- [ ] Deduplication prevents event flooding
- [ ] Sessions are built from event sequences
- [ ] Episodes group related events across sources
- [ ] Stuck detector fires at correct friction thresholds
- [ ] REST API serves all documented endpoints
- [ ] WebSocket alerts stream to connected clients
- [ ] Data retention auto-purges old events
- [ ] All unit tests pass

---

## 11. What This Member Owns

- WebSocket event server (receives from sensors)
- Event normalization and deduplication
- Event store (SQLite)
- Session builder
- Episode grouper
- Intent classifier (rule-based)
- Stuck detector (rule-based)
- Friction scorer
- Behavioral analysis engine
- REST API for data queries
- WebSocket alert stream for real-time notifications
- Data retention / purging logic

---

## 12. What This Member Does NOT Own

- Sensor implementations (Members 1, 2, 3)
- AI inference / model management (Member 5)
- Knowledge graph (Member 5)
- Embedding generation (Member 5)
- User interface / notifications (Member 6)
- Tutor / hint generation (Member 6)
- Roadmap building (Member 6)
- Automation engine (Member 6)
