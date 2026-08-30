# Member 1 — Browser Sensor

> **Owner**: Member 1
> **Folder**: `member-1_browser-sensor/`
> **Status**: Phase 0 — Documentation

---

## 1. Component Responsibility

Member 1 owns the **Firefox WebExtension** that observes browser activity and emits structured events to the Tesseract Core Engine.

This is a **sensor** — it collects and emits events. It does **not** analyze, classify, or interpret events. All intelligence is downstream (Members 4–6).

---

## 2. Features

### 2.1 Tab Tracking
- Detect tab creation, activation, deactivation, and closure
- Capture URL, title, and time spent per tab
- Track navigation within a tab (URL changes)

### 2.2 Search Monitoring
- Detect search queries on major search engines (Google, Bing, DuckDuckGo, etc.)
- Capture the search query text and engine used

### 2.3 YouTube Detection
- Detect when a user is watching a YouTube video
- Capture video URL, title, channel name
- Track watch duration vs. total video length

### 2.4 Page Content Extraction (lightweight)
- Extract page title and meta description
- Detect page language and category (if available)
- Do NOT extract full page body content (privacy)

### 2.5 Navigation Pattern Tracking
- Track `from_url → to_url` transitions
- Detect repeated visits to the same domain/topic

### 2.6 Bookmark Tracking
- Detect when a user bookmarks a page
- Capture URL and title

### 2.7 WebSocket Event Emitter
- Establish persistent WebSocket connection to Core Engine (`ws://localhost:9700/events`)
- Emit all events as JSON conforming to the TesseractEvent schema
- Handle connection loss, reconnection, and event buffering

---

## 3. Internal Architecture

```
┌─────────────────────────────────────────────┐
│          Firefox WebExtension               │
│                                             │
│  ┌───────────┐  ┌───────────┐  ┌─────────┐│
│  │Tab Tracker│  │Search     │  │YouTube  ││
│  │           │  │Monitor    │  │Detector ││
│  └─────┬─────┘  └─────┬─────┘  └────┬────┘│
│        │              │              │      │
│        ↓              ↓              ↓      │
│  ┌──────────────────────────────────────┐  │
│  │         Event Formatter              │  │
│  │   (Converts to TesseractEvent JSON)  │  │
│  └──────────────────┬───────────────────┘  │
│                     ↓                       │
│  ┌──────────────────────────────────────┐  │
│  │       WebSocket Client               │  │
│  │   (Buffers, sends, reconnects)       │  │
│  └──────────────────┬───────────────────┘  │
│                     ↓                       │
└─────────────────────┼───────────────────────┘
                      ↓
              ws://localhost:9700/events
              (Member 4 — Core Engine)
```

---

## 4. Inputs

| Input | Source | Description |
|:---|:---|:---|
| Tab events | `browser.tabs` API | `onCreated`, `onUpdated`, `onActivated`, `onRemoved` |
| History events | `browser.history` API | `onVisited` |
| Bookmark events | `browser.bookmarks` API | `onCreated` |
| Page content | Content scripts | Title, meta, URL |
| WebSocket config | `.env` | Core Engine host/port, shared secret |

---

## 5. Outputs

All outputs are **TesseractEvent** JSON messages sent over WebSocket to Member 4.

| Event Type | Payload Fields |
|:---|:---|
| `tab_activated` | `url`, `title`, `tab_id` |
| `tab_closed` | `url`, `title`, `tab_id`, `duration_ms` |
| `page_loaded` | `url`, `title`, `load_time_ms` |
| `search_performed` | `query`, `engine` |
| `youtube_watching` | `video_url`, `video_title`, `channel`, `duration_s`, `watch_time_s` |
| `navigation` | `from_url`, `to_url` |
| `bookmark_added` | `url`, `title` |

---

## 6. APIs Used

### Firefox WebExtension APIs

| API | Permission | Purpose |
|:---|:---|:---|
| `browser.tabs` | `tabs` | Tab lifecycle tracking |
| `browser.history` | `history` | Page visit detection |
| `browser.bookmarks` | `bookmarks` | Bookmark tracking |
| `browser.webNavigation` | `webNavigation` | Navigation event tracking |
| `browser.idle` | `idle` | Detect user idle state |

### External Communication

| Protocol | Endpoint | Direction |
|:---|:---|:---|
| WebSocket | `ws://localhost:9700/events` | Extension → Core Engine |

---

## 7. Data Structures

### TesseractEvent (output format)

```json
{
  "event_id": "uuid-v4",
  "source": "browser",
  "event_type": "tab_activated",
  "timestamp": "2026-08-30T10:15:30.000Z",
  "payload": {
    "url": "https://example.com",
    "title": "Example Page",
    "tab_id": 42
  },
  "metadata": {
    "session_id": "uuid-v4",
    "confidence": 1.0,
    "privacy_level": "local_only"
  }
}
```

---

## 8. Dependencies

### Internal Dependencies (at runtime)

| Dependency | Member | Interface |
|:---|:---|:---|
| Core Engine WebSocket server | Member 4 | `ws://localhost:9700/events` |

### External Dependencies

| Package | Purpose |
|:---|:---|
| `web-ext` | Firefox extension development/testing tool |
| `uuid` (or built-in `crypto.randomUUID()`) | Event ID generation |

---

## 9. Interfaces

### 9.1 Outbound: Sensor → Core Engine

- **Interface Name**: `SensorEventStream`
- **Owner**: Member 4 (server)
- **Consumer**: Member 1 (client)
- **Protocol**: WebSocket
- **Endpoint**: `ws://localhost:9700/events`
- **Data Format**: JSON (TesseractEvent)
- **Auth**: `Authorization: Bearer <TESSERACT_SHARED_SECRET>` header on WS handshake

---

## 10. Testing

### Unit Tests
- Tab tracker correctly formats events from `browser.tabs` API mocks
- Search monitor correctly parses Google/Bing/DuckDuckGo URLs
- YouTube detector correctly identifies YouTube video pages and extracts metadata
- Event formatter produces valid TesseractEvent JSON
- WebSocket client buffers events when disconnected and flushes on reconnect

### Integration Tests (Phase 2+)
- Extension connects to Member 4 WebSocket server
- Events arrive at Core Engine with correct schema
- Reconnection works after Core Engine restart

---

## 11. Definition of Done

- [ ] Firefox extension loads in Firefox without errors
- [ ] All event types listed above are captured and emitted
- [ ] Events conform to TesseractEvent schema
- [ ] WebSocket connection to Core Engine works reliably
- [ ] Events buffer during disconnection and flush on reconnect
- [ ] YouTube watch-time tracking is accurate
- [ ] Search query extraction works for Google, Bing, DuckDuckGo
- [ ] All unit tests pass
- [ ] Mozilla data disclosure requirements are documented
- [ ] Extension can be loaded as a temporary add-on for development

---

## 12. What This Member Owns

- Firefox WebExtension (all source code)
- Browser event capture logic
- Search query parsing
- YouTube detection and tracking
- WebSocket client (browser-side)
- Extension manifest and permissions
- Extension packaging/build

---

## 13. What This Member Does NOT Own

- Event analysis or interpretation (Member 4)
- WebSocket server (Member 4)
- Intent classification (Member 4)
- AI inference (Member 5)
- Knowledge graph (Member 5)
- User interface / notifications (Member 6)
- Any non-browser sensors (Members 2, 3)
