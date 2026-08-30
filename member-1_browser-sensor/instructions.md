# Member 1 — Browser Sensor: Development Instructions

> **Owner**: Member 1
> **Language**: JavaScript (WebExtension)
> **Runtime**: Firefox Browser

---

## 1. Environment Setup

### 1.1 Prerequisites

| Tool | Version | Installation |
|:---|:---|:---|
| Node.js | 20 LTS+ | [nodejs.org](https://nodejs.org) |
| npm | 10+ | Comes with Node.js |
| Firefox | 128+ | [mozilla.org](https://www.mozilla.org/firefox/) |
| Firefox Developer Edition | Latest | Recommended for debugging |
| Git | 2.40+ | [git-scm.com](https://git-scm.com) |

### 1.2 Initial Setup

```bash
cd member-1_browser-sensor

# Install dependencies
npm install

# Copy environment config
copy ..\env\member-1\.env.example .env
# Edit .env with your local settings
```

---

## 2. Dependencies

### 2.1 npm Packages

```json
{
  "devDependencies": {
    "web-ext": "^8.0.0",
    "eslint": "^9.0.0",
    "prettier": "^3.0.0",
    "jest": "^29.0.0"
  }
}
```

### 2.2 Firefox WebExtension APIs (no npm install needed)

- `browser.tabs`
- `browser.history`
- `browser.bookmarks`
- `browser.webNavigation`
- `browser.idle`
- `browser.storage.local`
- `browser.runtime`

---

## 3. Configuration

### 3.1 Manifest (manifest.json)

The extension uses **Manifest V3** (Firefox supports both V2 and V3; use V3 for forward compatibility).

Key permissions:
```json
{
  "permissions": [
    "tabs",
    "history",
    "bookmarks",
    "webNavigation",
    "idle",
    "storage"
  ],
  "host_permissions": [
    "<all_urls>"
  ]
}
```

### 3.2 Environment Variables

Located in `../env/member-1/.env.example`:

```env
TESSERACT_CORE_WS_URL=ws://localhost:9700/events
TESSERACT_SHARED_SECRET=
TESSERACT_BUFFER_SIZE=100
TESSERACT_RECONNECT_INTERVAL_MS=5000
```

The extension reads these from `browser.storage.local` (set via an options page or injected during build).

---

## 4. Development Commands

```bash
# Lint
npx eslint src/

# Format
npx prettier --write src/

# Run tests
npm test

# Build extension (produces web-ext-artifacts/)
npx web-ext build --source-dir=src/

# Run extension in Firefox (temporary install with live reload)
npx web-ext run --source-dir=src/ --firefox=firefox

# Run with Firefox Developer Edition
npx web-ext run --source-dir=src/ --firefox=firefoxdeveloperedition
```

---

## 5. Testing

### 5.1 Unit Tests

```bash
npm test
```

Test files should be in `tests/` directory. Use Jest with browser API mocks.

Mock the `browser.*` APIs using a library like `webextensions-api-mock` or custom mocks.

### 5.2 Manual Testing

1. Run `npx web-ext run --source-dir=src/`
2. Open several tabs, perform searches, watch a YouTube video
3. Check browser console (`Ctrl+Shift+J`) for event logs
4. Verify WebSocket connection to Core Engine (or mock server)

### 5.3 Mock WebSocket Server (for independent development)

During Phase 1, use a simple mock WebSocket server to test events without Member 4's Core Engine:

```bash
# Use any WebSocket echo server or create a simple one with wscat
npx wscat -l 9700
```

---

## 6. Debugging

### 6.1 Extension Debugging

1. Open Firefox
2. Navigate to `about:debugging#/runtime/this-firefox`
3. Click "Load Temporary Add-on"
4. Select `src/manifest.json`
5. Click "Inspect" to open DevTools for the background script

### 6.2 Console Logging

Use structured logging:
```javascript
console.log('[TESSERACT][TabTracker]', { event_type: 'tab_activated', url: '...' });
```

---

## 7. API Requirements

### 7.1 Outbound WebSocket

| Property | Value |
|:---|:---|
| Protocol | WebSocket |
| Endpoint | `ws://localhost:9700/events` |
| Auth | `Authorization: Bearer <secret>` on handshake |
| Payload | TesseractEvent JSON |
| Reconnect | Auto-reconnect with exponential backoff |
| Buffer | Queue events locally when disconnected (max 100) |

---

## 8. Git Instructions

### 8.1 Branch Naming

```
member-1/{type}-{description}
```

Examples:
- `member-1/feat-tab-tracking`
- `member-1/feat-youtube-detection`
- `member-1/fix-reconnect-logic`

### 8.2 Commit Convention

```
[M1] type: short description
```

Examples:
- `[M1] feat: add tab lifecycle tracking`
- `[M1] fix: handle rapid tab switching`

### 8.3 Folder Discipline

**You may ONLY modify files inside `member-1_browser-sensor/`.**

If you need changes in another member's folder or root files, create an issue or discuss with the team. Do NOT modify other folders.

---

## 9. Integration Instructions (Phase 2+)

1. Ensure Member 4's Core Engine is running on port 9700
2. Load the extension in Firefox
3. Browse normally — events should appear in Core Engine logs
4. Verify all event types are received with correct schemas
5. Test reconnection by restarting Core Engine while the extension is active

---

## 10. Mozilla Data Disclosure

As of 2025–2026, Firefox requires extensions to disclose data collection:

1. Declare data collection in `manifest.json` (data collection disclosure fields)
2. Categorize data as "personal" (browsing history, search terms) or "technical"
3. Ensure the extension's listing page clearly explains what data is collected and why
4. All collected data must stay local (transmitted only to `localhost`)
5. User consent must be obtained before any observation begins
