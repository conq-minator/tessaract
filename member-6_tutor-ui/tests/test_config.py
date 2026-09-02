from tutor_ui.config import load_config

def test_load_config_defaults(monkeypatch):
    # clear env vars that might affect config
    for key in ["TESSERACT_UI_HOST", "TESSERACT_UI_PORT"]:
        monkeypatch.delenv(key, raising=False)
        
    config = load_config()
    assert config.host == "localhost"
    assert config.port == 9702
