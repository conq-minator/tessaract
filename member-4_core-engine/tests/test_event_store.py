"""
Test SQLite Event Store.
"""

from pathlib import Path

from core_engine.event_store import EventStore
from core_engine.models import Episode, Session, TesseractEvent


def test_event_store_lifecycle(tmp_path: Path):
    db_file = tmp_path / "test_core.db"
    store = EventStore(db_file)

    # 1. Insert event
    event = TesseractEvent(
        source="vscode",
        event_type="diagnostic_error",
        payload={"error_message": "Undefined symbol foo"},
    )
    store.insert_event(event)

    assert store.get_event_count() == 1
    recent = store.get_recent_events(limit=10)
    assert len(recent) == 1
    assert recent[0]["event_type"] == "diagnostic_error"

    # 2. Insert and update session
    session = Session(sources=["vscode"], primary_intent="debugging", topics=["c-programming"])
    store.insert_or_update_session(session)

    fetched_session = store.get_session(session.session_id)
    assert fetched_session is not None
    assert fetched_session["primary_intent"] == "debugging"
    assert "c-programming" in fetched_session["topics"]

    # 3. Insert and update episode
    episode = Episode(topic="pointers", outcome="ongoing", friction_score=0.45)
    store.insert_or_update_episode(episode)

    recent_episodes = store.get_recent_episodes(limit=5)
    assert len(recent_episodes) == 1
    assert recent_episodes[0]["topic"] == "pointers"

    # 4. Analytics
    analytics = store.get_analytics_summary()
    assert analytics["total_events"] == 1
    assert analytics["total_sessions"] == 1
    assert analytics["total_episodes"] == 1
