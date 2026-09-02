import argparse
import asyncio
import logging
import os
import signal
import threading
import time
from aiohttp import web

from tutor_ui.app import create_app
from tutor_ui.utils.logging import setup_logging
from tutor_ui.config import load_config
from tutor_ui.tray.tray_app import start_tray_in_background

logger = logging.getLogger("tesseract.tutor_ui.main")


def _run_aiohttp_in_thread(app: web.Application, host: str, port: int, ready: threading.Event) -> None:
    """
    Run the aiohttp server in a background thread with its own event loop.
    Sets the *ready* event once the server is listening.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())

    site = web.TCPSite(runner, host, port)
    loop.run_until_complete(site.start())
    logger.info("aiohttp server listening on http://%s:%s", host, port)
    ready.set()

    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(runner.cleanup())
        loop.close()


def _wait_for_server(host: str, port: int, timeout: float = 10.0) -> bool:
    """Poll the /health endpoint until the server responds or timeout expires."""
    import urllib.request
    import urllib.error

    url = f"http://{host}:{port}/health"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2):
                return True
        except (urllib.error.URLError, OSError):
            time.sleep(0.15)
    return False


def main() -> None:
    """Entry point for the Tutor & UI service."""
    parser = argparse.ArgumentParser(description="Tesseract Tutor & UI Service")
    parser.add_argument(
        "--mock-data",
        action="store_true",
        help="Run with mock data (do not connect to Members 4 and 5)",
    )
    parser.add_argument(
        "--no-tray",
        action="store_true",
        help="Run without the system tray application",
    )
    parser.add_argument(
        "--no-desktop",
        action="store_true",
        help="Run in browser mode (open dashboard in default browser instead of native window)",
    )
    
    args = parser.parse_args()
    
    # Load config and setup logging
    config = load_config()
    setup_logging(config.log_level)

    # CLI flag overrides env var
    use_desktop = config.desktop_mode and not args.no_desktop
    
    logger.info(
        "Starting Tutor & UI Service",
        extra={"mock_data": args.mock_data, "no_tray": args.no_tray, "desktop": use_desktop},
    )
    
    app = create_app(config, mock_mode=args.mock_data)
    dashboard_url = f"http://{config.host}:{config.port}/overview"
    
    def on_quit():
        logger.info("Quit requested, sending shutdown signal...")
        try:
            os.kill(os.getpid(), signal.SIGINT)
        except Exception:
            os._exit(0)

    if use_desktop:
        # ── Desktop mode ───────────────────────────────────────────────
        # 1. Start aiohttp in a background thread
        server_ready = threading.Event()
        server_thread = threading.Thread(
            target=_run_aiohttp_in_thread,
            args=(app, config.host, config.port, server_ready),
            daemon=True,
        )
        server_thread.start()

        # 2. Wait for the server to be ready
        if not _wait_for_server(config.host, config.port):
            logger.error("aiohttp server did not start in time")
            return

        # 3. Create the native desktop window (import here to avoid
        #    pulling in pywebview when running in browser-only mode)
        from tutor_ui.desktop.window import DesktopWindow

        desktop_window = DesktopWindow(
            url=dashboard_url,
            title="Tesseract",
            width=config.window_width,
            height=config.window_height,
            on_closed=on_quit,
        )

        # 4. Start system tray with a reference to the desktop window
        if not args.no_tray:
            logger.info("Starting System Tray...")
            start_tray_in_background(
                port=config.port,
                on_quit=on_quit,
                desktop_window=desktop_window,
            )

        # 5. Start pywebview on the main thread (blocks until window is destroyed)
        try:
            desktop_window.start()
        except KeyboardInterrupt:
            logger.info("Shutting down service...")
    else:
        # ── Browser mode (original behaviour) ──────────────────────────
        if not args.no_tray:
            logger.info("Starting System Tray...")
            start_tray_in_background(port=config.port, on_quit=on_quit)

        try:
            web.run_app(app, host=config.host, port=config.port)
        except KeyboardInterrupt:
            logger.info("Shutting down service...")

if __name__ == "__main__":
    main()
