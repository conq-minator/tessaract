# Agent Learning Memory (Phase 4 Final)

This file contains learnings, gotchas, and design decisions recorded during the development of Member 6 (Tutor UI).

## Design Decisions
1. **Glassmorphism Theme**: Chosen to give a modern, premium feel. Implemented via `hsla()` background colors and `backdrop-filter: blur(12px)`.
2. **Vanilla JS over React**: Per project constraints, we stuck to Vanilla JS. To keep it clean, we used an ESModules-like pattern attached to a global `window.App` state object.
3. **SSE over WebSockets for UI**: While the backend connects to Member 4 via WebSockets (`alert_listener.py`), the connection from the browser to the backend uses Server-Sent Events (SSE). This is much simpler to implement on the frontend (auto-reconnects, unidirectional flow) and perfectly suited for push notifications.
4. **Pystray in Background Thread**: `pystray.Icon.run()` blocks the execution thread. Because we are using `aiohttp` (which requires the main thread for its event loop), we spawned the `pystray` tray app in a `threading.Thread(daemon=True)` in `__main__.py`.

## Gotchas & Workarounds
1. **AsyncMock vs MagicMock**: When writing tests for `aiohttp.ClientSession.get()`, using `AsyncMock` causes the method to return a coroutine instead of an asynchronous context manager. We had to use `MagicMock` and define `return_value = MockContextManager()` with `__aenter__` and `__aexit__` explicitly.
2. **Mock Data Wrapping**: When migrating from static mock endpoints to the service architecture, ensure the mock functions return raw data dicts without the `{"status": "success", "data": ...}` envelope, otherwise the routes will double-wrap them.
3. **Pillow for Dynamic Icons**: Generating base `.png` icons dynamically via PIL/Pillow saved us from needing binary image files committed to the repo initially.

## Future Development
- Member 4 (Core) must implement `GET /api/v1/episodes` for the history tab.
- Member 5 (AI) must implement the roadmap builder API.
- The `AutomationService` needs real workflow detection logic (Phase 4.6 was just a stub).

## Phase 3 Mock Data Deletion (Preserved for Future Reference)
*Note: This section summarizes the mock data transition from Phase 3 for when the modules are finally combined.*
- **Proposed Deletion**: The original static mock routes in `api.py` (e.g., hardcoded JSON responses) were proposed for deletion. 
- **Current Approach**: To keep the system independent during testing, the mock endpoints were not entirely deleted but instead moved behind a `--mock-data` toggle (handled by `mock_core` and `mock_ai`). 
- **Future Action**: When Member 6 is fully integrated with the real Members 4 and 5, this mock layer and the `--mock-data` fallback can be fully safely deleted.

## Final Code Trimmings (Backup)
*Note: During the final polish pass, several unused imports were removed to clean up static analysis warnings (flake8). These are recorded here in case they are needed for future debugging.*
- `src/tutor_ui/services/assistance.py`: Removed unused `Optional` from `typing`.
- `tests/conftest.py`: Removed unused `aiohttp.web`.
- `tests/test_clients.py`: Removed unused `patch` from `unittest.mock`.
- `tests/test_routes.py`: Removed duplicate `import pytest`.
- `tests/test_services.py`: Removed unused `import asyncio`.
- `tests/test_tray.py`: Removed unused `import pytest`.
