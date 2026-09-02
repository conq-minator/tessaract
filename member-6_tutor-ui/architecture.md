# Architecture & File Structure (Phase 4 Final)

The `tutor_ui` module is an aiohttp-based local web dashboard and system tray application for the Tesseract ecosystem.

## Technology Stack
- **Backend Framework**: `aiohttp` (async web server)
- **Templating**: `aiohttp-jinja2` (server-side rendering)
- **Frontend Core**: Vanilla HTML, CSS (CSS variables, flex/grid), and JavaScript (ESModules pattern without build step)
- **Frontend Visualization**: D3.js v7 (force-directed graphs), Chart.js v4
- **System Tray**: `pystray` (runs in a background daemon thread)
- **Testing**: `pytest` and `pytest-aiohttp`

## Directory Structure

```text
member-6_tutor-ui/
├── pyproject.toml              # Dependencies and scripts (tutor_ui entry point)
├── prd.md                      # Product requirements document
├── phases.md                   # Development phases (all completed)
├── rules.md                    # Engineering standards
├── architecture.md             # This file
├── memory.md                   # Agent learning memory
├── tests/                      # Pytest suite
│   ├── conftest.py
│   ├── test_clients.py
│   ├── test_routes.py
│   ├── test_services.py
│   └── test_tray.py
├── src/
│   └── tutor_ui/
│       ├── __init__.py
│       ├── __main__.py         # CLI entry point (starts aiohttp and tray)
│       ├── app.py              # aiohttp application factory & service registry
│       ├── config.py           # Environment and config loading
│       ├── clients/            # Outbound integration logic
│       │   ├── ai_client.py    # HTTP client for Member 5 (Port 9701)
│       │   ├── core_client.py  # HTTP client for Member 4 (Port 9700)
│       │   └── alert_listener.py # WebSocket client to Member 4 for live alerts
│       ├── mock/               # Mock data sources (for --mock-data flag)
│       ├── models/             # Data models
│       ├── routes/             # HTTP Route handlers
│       │   ├── api.py          # /api/* endpoints including SSE stream
│       │   ├── dashboard.py    # HTML view endpoints
│       │   └── health.py       # /health
│       ├── services/           # Business logic layer
│       │   ├── assistance.py
│       │   ├── automation.py
│       │   ├── notification.py
│       │   ├── permission.py
│       │   ├── recommendation.py
│       │   └── roadmap.py
│       ├── tray/               # System tray application
│       │   ├── icons/          # Programmatically generated PNG icons
│       │   └── tray_app.py     # pystray implementation
│       └── utils/              # Shared utilities (auth, logging)
├── static/                     # Static web assets
│   ├── assets/                 # SVGs and images
│   ├── css/                    # Modular CSS (main, components, knowledge-graph)
│   └── js/                     # Modular JS (app, api, components, pages)
└── templates/                  # Jinja2 HTML templates
    ├── base.html               # Master layout and global loader
    ├── components/             # Reusable UI partials (sidebar, modals, toasts)
    └── pages/                  # The 6 dashboard views
```

## Data Flow
1. **System Startup**: `__main__.py` starts the `pystray` icon in a background thread, then runs the `aiohttp` loop on the main thread.
2. **HTTP Requests**: The browser hits `GET /overview`. The `dashboard.py` router renders the Jinja template and sends it.
3. **Data Hydration**: The browser JS (`app.js`) fetches `/api/context`. The `api.py` router routes this to `AssistanceService`.
4. **Service Layer**: The `AssistanceService` queries the `CoreClient` for the real data or `mock_core` if in mock mode.
5. **Real-time Push**: Member 4 emits a WebSocket event to `AlertListener`, which pipes it to `NotificationManager`, which pushes it down the Server-Sent Events (SSE) `/api/stream` to the browser.
