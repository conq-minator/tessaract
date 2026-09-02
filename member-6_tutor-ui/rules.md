# Member 6 — Tutor & UI: Rules (Do's and Don'ts)

> **Owner**: Member 6  
> **Version**: 0.1.0  
> **Last Updated**: 2026-09-01

---

## 1. Folder Discipline

### ✅ DO

- Only modify files inside `member-6_tutor-ui/`
- Read other members' `contents.md` and `instructions.md` for interface specs
- Use documented API contracts to communicate with Members 4 and 5

### ❌ DON'T

- **NEVER** modify files in any other member's folder
- **NEVER** modify root-level files (`contents.md`, `instructions.md`, `.gitignore`, `README.md`) without team consensus
- **NEVER** copy code from another member's implementation into your folder

---

## 2. Libraries & Dependencies

### 2.1 Backend (Python)

#### ✅ ALLOWED

| Library | Purpose |
|:---|:---|
| `aiohttp` | HTTP server (dashboard backend) |
| `httpx` | Async HTTP client (calls to Members 4, 5) |
| `websockets` | WebSocket client (alerts from Member 4) |
| `jinja2` | HTML template rendering |
| `pystray` | System tray icon |
| `Pillow` | Tray icon image processing |
| `python-dotenv` | .env file loading |
| `uuid6` | UUID generation |
| `dataclasses` | Data structures (stdlib) |
| `logging` | Structured logging (stdlib) |
| `asyncio` | Async orchestration (stdlib) |
| `json` | JSON handling (stdlib) |
| `pathlib` | Path handling (stdlib) |

#### ❌ FORBIDDEN

| Library | Reason |
|:---|:---|
| Flask | Not async; aiohttp is the chosen server |
| Django | Too heavy; not needed for a local dashboard |
| FastAPI | Not the chosen server; stick to aiohttp |
| SQLAlchemy | Member 6 owns no database |
| requests | Use `httpx` (async-native) instead |
| Any ORM | Member 6 has no database |
| Any AI/ML lib | All AI goes through Member 5's API |
| `print()` for logging | Use `logging` module only |

### 2.2 Frontend (Browser)

#### ✅ ALLOWED

| Library | Load Method | Purpose |
|:---|:---|:---|
| D3.js (v7) | CDN | Knowledge graph visualization |
| Chart.js (v4) | CDN | Analytics charts |
| Vanilla JS | Native | All interactivity |
| HTML5 + CSS3 | Native | Structure and styling |
| Google Fonts (Inter) | CDN | Typography |

#### ❌ FORBIDDEN

| Library | Reason |
|:---|:---|
| React | Intentionally avoided — vanilla JS only |
| Vue.js | Intentionally avoided — vanilla JS only |
| Angular | Intentionally avoided — vanilla JS only |
| Svelte | Intentionally avoided — vanilla JS only |
| jQuery | Not needed with modern vanilla JS |
| Bootstrap | Pure custom CSS for design control |
| Tailwind CSS | Pure custom CSS for design control |
| Any CSS framework | Pure custom CSS for design control |
| Webpack / Vite | No build step for frontend — vanilla JS |
| npm packages (frontend) | CDN only for D3 and Chart.js |

---

## 3. Code Style

### 3.1 Python

| Tool | Setting |
|:---|:---|
| Formatter | **Black** (line length 100) |
| Linter | **Ruff** |
| Type Checker | **mypy** (strict mode) |
| Docstrings | Google style |
| Import Sorting | `isort` (handled by Ruff) |

#### Rules

- All functions **must** have type annotations
- All public functions **must** have Google-style docstrings
- All modules **must** have a module-level docstring
- Use `pathlib.Path` instead of `os.path`
- Use `dataclasses` or `TypedDict` for structured data, not raw dicts
- Use `enum.Enum` for finite sets of values (e.g., autonomy levels, themes)
- Prefer `async def` over sync functions in the server path
- Maximum function length: ~50 lines (refactor if longer)

### 3.2 JavaScript

| Rule | Standard |
|:---|:---|
| Style | Modern ES6+ (const/let, arrow functions, template literals) |
| No `var` | Use `const` by default, `let` when reassignment is needed |
| Naming | camelCase for variables/functions, PascalCase for classes |
| DOM | Use `document.querySelector` / `querySelectorAll` |
| Events | Use `addEventListener`, never inline `onclick` |
| Modules | Use ES modules (`<script type="module">`) where supported |
| Fetch | Use `fetch()` API for all HTTP requests |

### 3.3 CSS

| Rule | Standard |
|:---|:---|
| Variables | Define all colors, spacing, fonts as CSS custom properties |
| Naming | BEM-inspired: `.component__element--modifier` |
| Units | `rem` for font sizes, `px` for borders/shadows, `%` for layouts |
| No `!important` | Avoid unless absolutely necessary |
| Media queries | Mobile-first breakpoints (min-width) |

### 3.4 HTML

| Rule | Standard |
|:---|:---|
| Semantics | Use `<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<footer>` |
| Accessibility | All interactive elements must have ARIA labels |
| IDs | All interactive elements must have unique, descriptive IDs |
| Forms | All inputs must have associated `<label>` elements |
| Images | All `<img>` must have `alt` attributes |

---

## 4. Error Handling

### ✅ DO

```python
# ✅ Catch specific exceptions
try:
    response = await self.client.get(url)
    response.raise_for_status()
except httpx.ConnectError:
    logger.error("Cannot connect to Core Engine", extra={"url": url})
    return default_value
except httpx.HTTPStatusError as e:
    logger.warning("Core Engine returned error", extra={"status": e.response.status_code})
    return default_value
```

```python
# ✅ Use structured logging
logger = logging.getLogger("tesseract.tutor_ui.assistance")
logger.info("Hint generated", extra={"topic": topic, "level": level, "friction": score})
```

```python
# ✅ Graceful degradation
async def get_context(self) -> Context:
    """Fetch current context, falling back to empty context if unavailable."""
    try:
        return await self.core_client.get_current_context()
    except ServiceUnavailableError:
        logger.warning("Core Engine unavailable, using empty context")
        return Context.empty()
```

### ❌ DON'T

```python
# ❌ Never use bare except
try:
    data = await fetch()
except:  # NEVER DO THIS
    pass

# ❌ Never use print for logging
print("something happened")  # NEVER DO THIS

# ❌ Never swallow errors silently
try:
    risky_operation()
except Exception:
    pass  # NEVER DO THIS — at minimum, log the error

# ❌ Never catch and re-raise without adding context
try:
    operation()
except Exception as e:
    raise e  # Pointless — either handle it or let it propagate
```

### Error Handling Rules

1. **Always catch specific exceptions** — never bare `except` or `except Exception` without logging
2. **Always log errors** with structured data (extra kwargs)
3. **Graceful degradation** — if a upstream service is down, show a fallback UI, don't crash
4. **Return defaults** for non-critical failures (e.g., empty context if Member 4 is down)
5. **Raise for critical failures** — if the server can't start, fail loudly
6. **Never swallow exceptions silently** — at minimum, `logger.exception()`
7. **HTTP errors from upstream**: Log, return fallback, show user-friendly message

---

## 5. Security Rules

### ✅ DO

- Load secrets from `.env` via `python-dotenv`
- Use shared-secret authentication for calls to Members 4 and 5
- Use `https://` for any cloud API calls
- Validate all user input from the dashboard
- Sanitize data before rendering in Jinja2 templates (auto-escaping is on by default)

### ❌ DON'T

- **NEVER** commit `.env` files to Git
- **NEVER** hardcode API keys, passwords, tokens, or secrets in source code
- **NEVER** log sensitive data (passwords, tokens, PII)
- **NEVER** trust raw user input — validate and sanitize
- **NEVER** disable Jinja2 auto-escaping
- **NEVER** expose internal error details to the browser (stack traces, file paths)

---

## 6. Git Rules

### Branch Naming

```
member-6/{type}-{description}
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

Examples:
- `member-6/feat-dashboard-overview`
- `member-6/fix-notification-cooldown`
- `member-6/docs-update-architecture`

### Commit Convention

```
[M6] type: short description

Optional longer description explaining why.
```

Examples:
- `[M6] feat: add knowledge graph page with D3.js visualization`
- `[M6] fix: respect notification cooldown setting`
- `[M6] test: add permission guard unit tests`

### Pull Requests

1. All PRs target the `develop` branch
2. PR title follows commit convention
3. PR description explains **what** and **why**
4. All tests must pass
5. Use **squash merge** into `develop`

---

## 7. Testing Rules

### ✅ DO

- Write unit tests for every public function in `services/`
- Use `pytest` with `pytest-asyncio` for async tests
- Use `pytest-aiohttp` for route/endpoint tests
- Use fixtures (`conftest.py`) for shared mocks and test data
- Test both happy paths and error paths
- Test permission guard edge cases thoroughly
- Test notification cooldown logic
- Aim for >80% code coverage on `services/`

### ❌ DON'T

- Don't test private/internal functions directly — test through public API
- Don't make real HTTP calls in unit tests — always mock `clients/`
- Don't test Jinja2 template rendering in unit tests — that's a UI test
- Don't skip error-path tests — they catch the most bugs

---

## 8. Logging Rules

### Logger Naming

```python
# Always use hierarchical logger names under the tesseract namespace
logger = logging.getLogger("tesseract.tutor_ui")              # module-level
logger = logging.getLogger("tesseract.tutor_ui.assistance")    # service-level
logger = logging.getLogger("tesseract.tutor_ui.clients.core")  # client-level
```

### Log Levels

| Level | Use For |
|:---|:---|
| `DEBUG` | Detailed diagnostic info (request/response payloads, state changes) |
| `INFO` | Normal operations (server started, hint generated, settings changed) |
| `WARNING` | Recoverable issues (upstream timeout, using fallback data) |
| `ERROR` | Failed operations that need attention (cannot connect, invalid data) |
| `CRITICAL` | Server cannot start, unrecoverable state |

### Format

Always use structured logging with `extra` kwargs:

```python
logger.info("Hint generated", extra={
    "topic": "c-pointers",
    "level": 2,
    "friction_score": 0.73,
    "notification_id": str(notification_id),
})
```

---

## 9. API Client Rules

### ✅ DO

- Always use `async with httpx.AsyncClient()` (or share a session)
- Set reasonable timeouts (5s for data queries, 15s for AI generation)
- Include shared-secret header in all upstream requests
- Handle connection errors gracefully (return fallback data)
- Log all failed API calls with status code and URL

### ❌ DON'T

- Don't create a new `httpx.AsyncClient` per request — reuse sessions
- Don't retry endlessly — max 3 retries with exponential backoff
- Don't block the event loop with synchronous HTTP calls
- Don't hardcode URLs — construct from config (host + port)

---

## 10. Frontend Rules

### ✅ DO

- Keep JS files under 300 lines — split into modules
- Use `fetch()` with proper error handling for all API calls
- Show loading states while fetching data
- Show error states when API calls fail
- Use CSS transitions for smooth interactions (200–300ms)
- Support keyboard navigation for all interactive elements

### ❌ DON'T

- Don't use `document.write()`
- Don't use inline styles — use CSS classes
- Don't use inline event handlers (`onclick="..."`) — use `addEventListener`
- Don't manipulate DOM on every frame — batch updates
- Don't block rendering with synchronous operations
