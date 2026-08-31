"""
Entrypoint for Tesseract Core Engine.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import signal
import sys

from .app import CoreEngineApp
from .config import get_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tesseract Core Engine Service")
    parser.add_argument(
        "--mock-ai", action="store_true", help="Use mock AI responses for standalone testing"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Logging level",
    )
    parser.add_argument(
        "--host", default=None, help="Host to bind (default from .env or localhost)"
    )
    parser.add_argument("--port", type=int, default=None, help="Port to bind (default 9700)")
    return parser.parse_args()


def configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def async_main() -> None:
    args = parse_args()
    config = get_config()

    if args.host:
        config.host = args.host
    if args.port:
        config.port = args.port
    if args.log_level:
        config.log_level = args.log_level

    configure_logging(config.log_level)

    app = CoreEngineApp(config=config, mock_ai=args.mock_ai)
    await app.start()

    stop_event = asyncio.Event()

    def signal_handler() -> None:
        stop_event.set()

    if sys.platform != "win32":
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

    try:
        if sys.platform == "win32":
            # On Windows, keep running with periodic sleep so KeyboardInterrupt is caught
            while not stop_event.is_set():
                await asyncio.sleep(1)
        else:
            await stop_event.wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await app.stop()


def main() -> None:
    with contextlib.suppress(KeyboardInterrupt, SystemExit):
        asyncio.run(async_main())


if __name__ == "__main__":
    main()
