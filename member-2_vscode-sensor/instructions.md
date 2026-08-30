# Member 2 — VS Code Sensor: Development Instructions

> **Owner**: Member 2
> **Language**: TypeScript
> **Runtime**: VS Code Extension Host

---

## 1. Environment Setup

### 1.1 Prerequisites

| Tool | Version | Installation |
|:---|:---|:---|
| Node.js | 20 LTS+ | [nodejs.org](https://nodejs.org) |
| npm | 10+ | Comes with Node.js |
| VS Code | 1.90+ | [code.visualstudio.com](https://code.visualstudio.com) |
| VS Code Insiders | Latest | Recommended for testing |
| Git | 2.40+ | [git-scm.com](https://git-scm.com) |

### 1.2 Initial Setup

```bash
cd member-2_vscode-sensor

# Install dependencies
npm install

# Copy environment config
copy ..\env\member-2\.env.example .env
# Edit .env with your local settings

# Compile TypeScript
npm run compile
```

---

## 2. Dependencies

### 2.1 npm Packages

```json
{
  "dependencies": {
    "ws": "^8.0.0",
    "uuid": "^10.0.0"
  },
  "devDependencies": {
    "@types/vscode": "^1.90.0",
    "@types/ws": "^8.0.0",
    "@types/uuid": "^10.0.0",
    "typescript": "^5.5.0",
    "eslint": "^9.0.0",
    "prettier": "^3.0.0",
    "@vscode/test-electron": "^2.4.0",
    "mocha": "^10.0.0",
    "@types/mocha": "^10.0.0"
  }
}
```

### 2.2 VS Code API

Declared in `package.json` under `engines.vscode`:
```json
{
  "engines": {
    "vscode": "^1.90.0"
  }
}
```

---

## 3. Configuration

### 3.1 Extension Manifest (package.json)

Key fields:
```json
{
  "name": "tesseract-vscode-sensor",
  "displayName": "Tesseract VS Code Sensor",
  "description": "Developer activity sensor for Tesseract AI Copilot",
  "version": "0.1.0",
  "engines": { "vscode": "^1.90.0" },
  "activationEvents": ["onStartupFinished"],
  "main": "./out/extension.js",
  "contributes": {
    "commands": [
      {
        "command": "tesseract.toggleSensor",
        "title": "Tesseract: Toggle Sensor"
      }
    ]
  }
}
```

### 3.2 Environment Variables

Located in `../env/member-2/.env.example`:

```env
TESSERACT_CORE_WS_URL=ws://localhost:9700/events
TESSERACT_SHARED_SECRET=
TESSERACT_BUFFER_SIZE=100
TESSERACT_RECONNECT_INTERVAL_MS=5000
TESSERACT_TERMINAL_CAPTURE=true
TESSERACT_EDIT_DEBOUNCE_MS=2000
```

Configuration is read from VS Code settings (`vscode.workspace.getConfiguration('tesseract')`) or from a `.env` file.

---

## 4. Development Commands

```bash
# Compile TypeScript
npm run compile

# Watch mode (recompile on save)
npm run watch

# Lint
npx eslint src/

# Format
npx prettier --write src/

# Run tests
npm test

# Package extension (produces .vsix)
npx @vscode/vsce package
```

---

## 5. Testing

### 5.1 Unit Tests

```bash
npm test
```

Use Mocha + `@vscode/test-electron` for testing within the VS Code environment.

### 5.2 Manual Testing

1. Open VS Code with this extension folder
2. Press `F5` to launch Extension Development Host
3. In the new VS Code window, open a project, edit files, run code, trigger errors
4. Check the Output panel (`Tesseract Sensor` channel) for event logs
5. Verify WebSocket connection to Core Engine (or mock server)

### 5.3 Mock WebSocket Server

During Phase 1, test without Member 4:

```bash
npx wscat -l 9700
```

---

## 6. Debugging

### 6.1 Extension Debugging

1. Open `member-2_vscode-sensor/` in VS Code
2. Go to Run and Debug panel (`Ctrl+Shift+D`)
3. Select "Launch Extension" configuration
4. Press F5
5. Set breakpoints in TypeScript source files
6. Use the Debug Console and Output panel for logs

### 6.2 Logging

Use the VS Code Output Channel:
```typescript
const output = vscode.window.createOutputChannel('Tesseract Sensor');
output.appendLine(`[TabTracker] File opened: ${document.fileName}`);
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
| Reconnect | Auto-reconnect with exponential backoff (max 30s) |
| Buffer | Queue events locally when disconnected (max 100) |

### 7.2 Terminal Output Capture

`vscode.window.onDidWriteTerminalData` may be experimental. If unavailable:
- Fallback: Use `child_process` for tasks launched by the extension
- Fallback: Parse task execution results via `vscode.tasks` API
- Document API stability status in the extension README

---

## 8. Model Requirements

**None.** This is a pure sensor component. No AI models are used.

---

## 9. Git Instructions

### 9.1 Branch Naming

```
member-2/{type}-{description}
```

Examples:
- `member-2/feat-editor-tracking`
- `member-2/feat-terminal-capture`
- `member-2/fix-diagnostic-severity`

### 9.2 Commit Convention

```
[M2] type: short description
```

### 9.3 Folder Discipline

**You may ONLY modify files inside `member-2_vscode-sensor/`.**

---

## 10. Integration Instructions (Phase 2+)

1. Ensure Member 4's Core Engine is running on port 9700
2. Launch the extension (F5 in VS Code)
3. Perform coding activities in the Extension Development Host
4. Verify events appear in Core Engine logs
5. Test rapid editing — confirm debouncing works
6. Test terminal commands — confirm exit codes are captured
7. Test error detection — introduce a syntax error, verify `error_detected` event
