from unittest.mock import MagicMock
from tutor_ui.tray.tray_app import TrayApp

def test_tray_app_initialization():
    mock_quit = MagicMock()
    app = TrayApp(port=9702, on_quit=mock_quit)
    
    assert app.port == 9702
    assert not app.is_paused
    
    # Test pause toggle
    app.toggle_pause(None, None)
    assert app.is_paused
    
    # Test quit
    app.quit_app(None, None)
    mock_quit.assert_called_once()
