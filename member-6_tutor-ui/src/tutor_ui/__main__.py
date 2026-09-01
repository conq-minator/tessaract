import argparse
import asyncio
import logging
import os
import signal
from aiohttp import web

from tutor_ui.app import create_app
from tutor_ui.utils.logging import setup_logging
from tutor_ui.config import load_config
from tutor_ui.tray.tray_app import start_tray_in_background

logger = logging.getLogger("tesseract.tutor_ui.main")

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
    
    args = parser.parse_args()
    
    # Load config and setup logging
    config = load_config()
    setup_logging(config.log_level)
    
    logger.info("Starting Tutor & UI Service", extra={"mock_data": args.mock_data, "no_tray": args.no_tray})
    
    app = create_app(config, mock_mode=args.mock_data)
    
    def on_quit():
        logger.info("Tray quit requested, sending shutdown signal...")
        try:
            # Send SIGINT to gracefully shut down web.run_app()
            os.kill(os.getpid(), signal.SIGINT)
        except Exception:
            os._exit(0)

    # Start the system tray app if not disabled
    if not args.no_tray:
        logger.info("Starting System Tray...")
        start_tray_in_background(port=config.port, on_quit=on_quit)
    
    # Start the web server
    try:
        web.run_app(app, host=config.host, port=config.port)
    except KeyboardInterrupt:
        logger.info("Shutting down service...")

if __name__ == "__main__":
    main()
