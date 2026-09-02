"""
Test models and serialization.
"""

from core_engine.models import (
    Episode,
    EventMetadata,
    Session,
    TesseractEvent,
)


def test_tesseract_event_serialization():
    event = TesseractEvent(
        source="vscode",
        event_type="file_edited",
        payload={"file_path": "src/main.c", "lines": 10},
        metadata=EventMetadata(confidence=0.95, privacy_level="local_only"),
    )
    d = event.to_dict()
    assert d["source"] == "vscode"
    assert d["event_type"] == "file_edited"
    assert d["payload"]["file_path"] == "src/main.c"
    assert d["metadata"]["confidence"] == 0.95

    reconstructed = TesseractEvent.from_dict(d)
    assert reconstructed.event_id == event.event_id
    assert reconstructed.source == "vscode"
    assert reconstructed.payload["lines"] == 10


def test_session_serialization():
    session = Session(
        sources=["browser", "vscode"],
        primary_intent="debugging",
        topics=["c-programming", "pointers"],
    )
    d = session.to_dict()
    assert d["is_active"] is True
    assert "browser" in d["sources"]
    assert "pointers" in d["topics"]

    reconstructed = Session.from_dict(d)
    assert reconstructed.session_id == session.session_id
    assert reconstructed.primary_intent == "debugging"


def test_episode_serialization():
    episode = Episode(
        topic="pointers",
        intent="learning",
        outcome="ongoing",
        friction_score=0.65,
    )
    d = episode.to_dict()
    assert d["topic"] == "pointers"
    assert d["friction_score"] == 0.65

    reconstructed = Episode.from_dict(d)
    assert reconstructed.episode_id == episode.episode_id
    assert reconstructed.outcome == "ongoing"
