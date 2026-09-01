import os
import pystray
from PIL import Image
from typing import Callable, Optional
import webbrowser
import threading

class TrayApp:
    def __init__(self, port: int = 9702, on_quit: Optional[Callable] = None):
        self.port = port
        self.on_quit = on_quit
        
        # Load Icons
        self.icons_dir = os.path.join(os.path.dirname(__file__), "icons")
        self.icon_active = Image.open(os.path.join(self.icons_dir, "active.png"))
        self.icon_paused = Image.open(os.path.join(self.icons_dir, "paused.png"))
        
        self.is_paused = False
        
        # Setup Menu
        self.menu = pystray.Menu(
            pystray.MenuItem("Open Dashboard", self.open_dashboard),
            pystray.MenuItem("Pause Observation", self.toggle_pause, checked=lambda item: self.is_paused),
            pystray.MenuItem("Quit Tesseract", self.quit_app)
        )
        
        self.icon = pystray.Icon("Tesseract", self.icon_active, "Tesseract - Active", self.menu)
        
    def open_dashboard(self, icon, item):
        webbrowser.open(f"http://localhost:{self.port}/overview")
        
    def toggle_pause(self, icon, item):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.icon.icon = self.icon_paused
            self.icon.title = "Tesseract - Paused"
        else:
            self.icon.icon = self.icon_active
            self.icon.title = "Tesseract - Active"
        
    def quit_app(self, icon, item):
        self.icon.stop()
        if self.on_quit:
            self.on_quit()
            
    def run(self):
        """Run the pystray blocking loop."""
        self.icon.run()

def start_tray_in_background(port: int, on_quit: Callable):
    """Spawns the tray icon in a separate daemon thread to avoid blocking asyncio."""
    app = TrayApp(port=port, on_quit=on_quit)
    thread = threading.Thread(target=app.run, daemon=True)
    thread.start()
    return app
