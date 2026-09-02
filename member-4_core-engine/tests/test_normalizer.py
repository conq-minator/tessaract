"""
Test Event Normalizer and Deduplicator.
"""

from core_engine.normalizer import EventNormalizer


def test_normalizer_basic():
    normalizer = EventNormalizer(dedup_window_ms=2000)
    raw_data = {
        "source": "VSCode",
        "event_type": "file_edited",
        "payload": {"file_path": "src\\main.c", "lines": 5},
    }
    event = normalizer.normalize(raw_data)
    assert event is not None
    assert event.source == "vscode"
    assert event.payload["file_path"] == "src/main.c"


def test_normalizer_deduplication():
    normalizer = EventNormalizer(dedup_window_ms=2000)
    raw_data = {
        "source": "browser",
        "event_type": "search",
        "payload": {"query": "segmentation fault c", "url": "https://google.com"},
    }

    # First event should pass
    event1 = normalizer.normalize(raw_data)
    assert event1 is not None

    # Immediate second duplicate event should be filtered out
    event2 = normalizer.normalize(raw_data)
    assert event2 is None


def test_normalizer_rate_limiting():
    normalizer = EventNormalizer(dedup_window_ms=0, max_rate_per_second=3)
    # Send 5 events with distinct payloads
    accepted = 0
    for i in range(5):
        raw = {
            "source": "os",
            "event_type": f"app_{i}",
            "payload": {"count": i},
        }
        res = normalizer.normalize(raw)
        if res is not None:
            accepted += 1

    assert accepted == 3
