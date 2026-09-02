"""
Native desktop window for the Tesseract dashboard using pywebview.

This module wraps pywebview to display the aiohttp-served dashboard
inside a native OS window (EdgeChromium on Windows, WebKit on macOS/Linux)
instead of opening a browser tab.
"""

import logging
import threading
from typing import Callable, Optional

import webview  # pywebview

logger = logging.getLogger("tesseract.tutor_ui.desktop")


class DesktopWindow:
    """Manages a native desktop window that displays the Tesseract dashboard."""

    def __init__(
        self,
        url: str,
        title: str = "Tesseract",
        width: int = 1280,
        height: int = 850,
        on_closed: Optional[Callable] = None,
    ):
        self.url = url
        self.title = title
        self.width = width
        self.height = height
        self.on_closed = on_closed

        self._window: Optional[webview.Window] = None
        self._started = threading.Event()

    # -- Public API ----------------------------------------------------------

    def show(self) -> None:
        """Bring the native window to the foreground."""
        if self._window is not None:
            try:
                self._window.show()
                self._window.restore()  # un-minimize if minimized
            except Exception:
                logger.debug("Could not show window (may already be visible)")

    def hide(self) -> None:
        """Hide the native window without destroying it."""
        if self._window is not None:
            try:
                self._window.hide()
            except Exception:
                logger.debug("Could not hide window")

    def destroy(self) -> None:
        """Destroy the native window and release resources."""
        if self._window is not None:
            try:
                self._window.destroy()
            except Exception:
                logger.debug("Window already destroyed")

    def wait_until_started(self, timeout: float = 10.0) -> bool:
        """Block until the window has been created and is ready."""
        return self._started.wait(timeout=timeout)

    # -- Lifecycle (called from start()) -------------------------------------

    def _on_shown(self) -> None:
        """Callback fired once the webview window is first shown."""
        logger.info("Desktop window shown")
        self._started.set()

    def _on_closing(self) -> None:
        """
        Intercept the window close event.
        Hide the window instead of destroying it so the tray can bring it back.
        """
        logger.info("Desktop window close requested — hiding instead")
        self.hide()
        return False  # Returning False prevents the default close

    def _on_closed(self) -> None:
        """Called when the window is actually destroyed."""
        logger.info("Desktop window destroyed")
        if self.on_closed:
            self.on_closed()

    def start(self) -> None:
        """
        Create the pywebview window and start the GUI event loop.

        **This call blocks** until the window is destroyed, so it must be
        run on the main thread (required on macOS; safest on all platforms).
        """
        logger.info("Creating native desktop window → %s", self.url)

        self._window = webview.create_window(
            title=self.title,
            url=self.url,
            width=self.width,
            height=self.height,
            min_size=(800, 600),
            background_color="#0a0e17",
            text_select=True,
        )

        # Register event callbacks
        self._window.events.shown += self._on_shown
        self._window.events.closing += self._on_closing
        self._window.events.closed += self._on_closed

        # start() blocks until all windows are destroyed
        webview.start()
