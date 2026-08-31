"""
Test Session Builder.
"""

from pathlib import Path

from core_engine.event_store import EventStore
from core_engine.models import TesseractEvent
from core_engine.session_builder import SessionBuilder


def test_session_builder_lifecycle(tmp_path: Path):
    db_file = tmp_path / "test_session.db"
    store = EventStore(db_file)
    builder = SessionBuilder(event_store=store, idle_timeout_s=10)

    # 1. First event starts session
    event1 = TesseractEvent(
        source="vscode",
        event_type="file_edited",
        payload={"file_path": "src/pointers.c"},
    )
    s1 = builder.process_event(event1)
    assert s1.is_active is True
    assert s1.events_count == 1
    assert "vscode" in s1.sources
    assert "pointers" in s1.topics

    # 2. Second event associates with same session
    event2 = TesseractEvent(
        source="browser",
        event_type="search",
        payload={"query": "c pointer arithmetic"},
    )
    s2 = builder.process_event(event2)
    assert s2.session_id == s1.session_id
    assert s2.events_count == 2
    assert "browser" in s2.sources

    # 3. Explicit close
    closed = builder.close_current_session()
    assert closed is not None
    assert closed.is_active is False
