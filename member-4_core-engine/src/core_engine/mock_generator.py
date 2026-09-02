"""
Mock Event Generator for Tesseract Core Engine.
Emits a realistic learning & debugging episode sequence over WebSocket or REST.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging

import websockets

from .models import generate_uuid, utc_now_iso

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mock_generator")


EVENT_SCENARIO = [
    {
        "source": "os",
        "event_type": "app_switch",
        "payload": {"app_name": "Code", "window_title": "pointers.c - VS Code"},
        "delay": 1.0,
    },
    {
        "source": "vscode",
        "event_type": "file_edited",
        "payload": {
            "file_path": "src/pointers.c",
            "language": "c",
            "lines_changed": 15,
            "content_summary": "int *ptr; *ptr = 42;",
        },
        "delay": 1.5,
    },
    {
        "source": "vscode",
        "event_type": "build_run",
        "payload": {
            "file_path": "src/pointers.c",
            "command": "gcc pointers.c -o pointers && ./pointers",
            "exit_code": 139,
            "error_message": "Segmentation fault (core dumped)",
        },
        "delay": 2.0,
    },
    {
        "source": "vscode",
        "event_type": "build_run",
        "payload": {
            "file_path": "src/pointers.c",
            "command": "./pointers",
            "exit_code": 139,
            "error_message": "Segmentation fault (core dumped)",
        },
        "delay": 1.5,
    },
    {
        "source": "browser",
        "event_type": "search",
        "payload": {
            "url": "https://www.google.com/search?q=segmentation+fault+c+dereference+pointer",
            "query": "segmentation fault c dereference pointer",
            "engine": "google",
        },
        "delay": 2.0,
    },
    {
        "source": "browser",
        "event_type": "page_visited",
        "payload": {
            "url": "https://stackoverflow.com/questions/12345/c-segmentation-fault-uninitialized-pointer",
            "title": "Why does dereferencing an uninitialized pointer cause segmentation fault?",
        },
        "delay": 2.0,
    },
    {
        "source": "browser",
        "event_type": "youtube_watch",
        "payload": {
            "url": "https://www.youtube.com/watch?v=mock123",
            "title": "C Pointer Dereferencing and Memory Allocation Tutorial",
            "channel": "Code With C",
            "duration_watched_s": 180,
        },
        "delay": 2.5,
    },
    {
        "source": "vscode",
        "event_type": "file_edited",
        "payload": {
            "file_path": "src/pointers.c",
            "language": "c",
            "content_summary": "int val = 42; int *ptr = &val; *ptr = 100;",
        },
        "delay": 1.5,
    },
    {
        "source": "vscode",
        "event_type": "build_run",
        "payload": {
            "file_path": "src/pointers.c",
            "command": "gcc pointers.c -o pointers && ./pointers",
            "exit_code": 0,
            "output": "Program executed successfully. Output: 100",
        },
        "delay": 1.0,
    },
]


async def run_ws_generator(host: str = "localhost", port: int = 9700, secret: str = "") -> None:
    uri = f"ws://{host}:{port}/events"
    headers = {"Authorization": f"Bearer {secret}"} if secret else None

    logger.info("Connecting to Core Engine WebSocket at %s...", uri)
    try:
        async with websockets.connect(uri, additional_headers=headers) as ws:
            logger.info("Connected! Emitting synthetic learning & debugging scenario events...")
            # Receive welcome message
            welcome = await ws.recv()
            logger.info("Server welcome: %s", welcome)

            for step in EVENT_SCENARIO:
                event = {
                    "event_id": generate_uuid(),
                    "source": step["source"],
                    "event_type": step["event_type"],
                    "timestamp": utc_now_iso(),
                    "payload": step["payload"],
                    "metadata": {"confidence": 1.0, "privacy_level": "local_only"},
                }
                logger.info("Sending [%s] %s ...", event["source"], event["event_type"])
                await ws.send(json.dumps(event))
                resp = await ws.recv()
                logger.info("Server Ack: %s", resp)
                delay_sec = float(str(step.get("delay", 1.0)))
                await asyncio.sleep(delay_sec)

            logger.info("Synthetic event sequence completed successfully!")
    except Exception as e:
        logger.error("Failed to connect or stream to WebSocket: %s", e)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tesseract Mock Event Generator")
    parser.add_argument("--host", default="localhost", help="Core Engine host")
    parser.add_argument("--port", type=int, default=9700, help="Core Engine port")
    parser.add_argument("--secret", default="", help="Shared secret token")
    args = parser.parse_args()

    asyncio.run(run_ws_generator(host=args.host, port=args.port, secret=args.secret))


if __name__ == "__main__":
    main()
