"""Tests for the desktop window module and desktop-mode integration."""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# DesktopWindow unit tests
# ---------------------------------------------------------------------------

class TestDesktopWindow:
    """Tests for DesktopWindow (mocking pywebview)."""

    @patch("tutor_ui.desktop.window.webview")
    def test_init_stores_config(self, mock_webview):
        from tutor_ui.desktop.window import DesktopWindow

        dw = DesktopWindow(
            url="http://localhost:9702/overview",
            title="Test",
            width=1024,
            height=768,
        )
        assert dw.url == "http://localhost:9702/overview"
        assert dw.title == "Test"
        assert dw.width == 1024
        assert dw.height == 768
        assert dw._window is None

    @patch("tutor_ui.desktop.window.webview")
    def test_start_creates_window(self, mock_webview):
        from tutor_ui.desktop.window import DesktopWindow

        mock_window = MagicMock()
        mock_webview.create_window.return_value = mock_window

        dw = DesktopWindow(url="http://localhost:9702/overview")
        dw.start()

        mock_webview.create_window.assert_called_once()
        call_kwargs = mock_webview.create_window.call_args
        assert call_kwargs.kwargs["url"] == "http://localhost:9702/overview"
        assert call_kwargs.kwargs["title"] == "Tesseract"
        mock_webview.start.assert_called_once()

    @patch("tutor_ui.desktop.window.webview")
    def test_show_calls_window_show(self, mock_webview):
        from tutor_ui.desktop.window import DesktopWindow

        dw = DesktopWindow(url="http://localhost:9702/overview")
        mock_win = MagicMock()
        dw._window = mock_win

        dw.show()
        mock_win.show.assert_called_once()
        mock_win.restore.assert_called_once()

    @patch("tutor_ui.desktop.window.webview")
    def test_hide_calls_window_hide(self, mock_webview):
        from tutor_ui.desktop.window import DesktopWindow

        dw = DesktopWindow(url="http://localhost:9702/overview")
        mock_win = MagicMock()
        dw._window = mock_win

        dw.hide()
        mock_win.hide.assert_called_once()

    @patch("tutor_ui.desktop.window.webview")
    def test_destroy_calls_window_destroy(self, mock_webview):
        from tutor_ui.desktop.window import DesktopWindow

        dw = DesktopWindow(url="http://localhost:9702/overview")
        mock_win = MagicMock()
        dw._window = mock_win

        dw.destroy()
        mock_win.destroy.assert_called_once()

    @patch("tutor_ui.desktop.window.webview")
    def test_on_closing_hides_instead_of_destroying(self, mock_webview):
        from tutor_ui.desktop.window import DesktopWindow

        dw = DesktopWindow(url="http://localhost:9702/overview")
        mock_win = MagicMock()
        dw._window = mock_win

        result = dw._on_closing()
        assert result is False  # prevent default close
        mock_win.hide.assert_called_once()

    @patch("tutor_ui.desktop.window.webview")
    def test_on_closed_fires_callback(self, mock_webview):
        from tutor_ui.desktop.window import DesktopWindow

        callback = MagicMock()
        dw = DesktopWindow(url="http://localhost:9702/overview", on_closed=callback)

        dw._on_closed()
        callback.assert_called_once()


# ---------------------------------------------------------------------------
# TrayApp integration with desktop window
# ---------------------------------------------------------------------------

class TestTrayDesktopIntegration:
    """Test that TrayApp correctly delegates to the desktop window."""

    def test_open_dashboard_uses_desktop_window(self):
        from tutor_ui.tray.tray_app import TrayApp

        mock_win = MagicMock()
        tray = TrayApp(port=9702, desktop_window=mock_win)

        tray.open_dashboard(None, None)
        mock_win.show.assert_called_once()

    @patch("tutor_ui.tray.tray_app.webbrowser")
    def test_open_dashboard_falls_back_to_browser(self, mock_wb):
        from tutor_ui.tray.tray_app import TrayApp

        tray = TrayApp(port=9702, desktop_window=None)
        tray.open_dashboard(None, None)
        mock_wb.open.assert_called_once_with("http://localhost:9702/overview")

    def test_quit_destroys_desktop_window(self):
        from tutor_ui.tray.tray_app import TrayApp

        mock_win = MagicMock()
        on_quit = MagicMock()
        tray = TrayApp(port=9702, on_quit=on_quit, desktop_window=mock_win)
        tray.icon = MagicMock()  # mock pystray icon to prevent actual tray ops

        tray.quit_app(None, None)
        mock_win.destroy.assert_called_once()
        on_quit.assert_called_once()


# ---------------------------------------------------------------------------
# CLI flag tests
# ---------------------------------------------------------------------------

class TestCLIFlags:
    """Test that --no-desktop flag is recognised."""

    def test_no_desktop_flag_parsed(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--no-desktop", action="store_true")
        args = parser.parse_args(["--no-desktop"])
        assert args.no_desktop is True

    def test_default_is_desktop_mode(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--no-desktop", action="store_true")
        args = parser.parse_args([])
        assert args.no_desktop is False
