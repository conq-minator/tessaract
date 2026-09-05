"""Tests for Core Engine Video Topic Extraction and Study Relevance Gate."""

import asyncio
import pytest
from pathlib import Path
from src.core_engine.ai_client import AIClient
from src.core_engine.app import CoreEngineApp
from src.core_engine.config import CoreConfig
from src.core_engine.models import TesseractEvent


@pytest.mark.asyncio
async def test_ai_client_classify_video():
    client = AIClient(mock_mode=True)
    study_res = await client.classify_video(
        title="Python Data Structures and Algorithms Course",
        channel="freeCodeCamp.org",
        description="Learn binary search trees, dynamic programming, and graphs in Python."
    )
    assert study_res["is_study_related"] is True
    assert "topic" in study_res

    non_study_res = await client.classify_video(
        title="Epic Gaming Montage & Funny Clips",
        channel="GamerZone",
        description="Watch the best fails and wins."
    )
    assert non_study_res["is_study_related"] is False


@pytest.mark.asyncio
async def test_core_engine_video_gate(tmp_path: Path):
    db_file = tmp_path / "test_events.db"
    config = CoreConfig(db_path_raw=str(db_file))
    app = CoreEngineApp(config=config, mock_ai=True)


    # 1. Non-study video event -> should be discarded
    non_study_event = TesseractEvent(
        source="browser",
        event_type="youtube_watching",
        payload={
            "url": "https://www.youtube.com/watch?v=12345",
            "title": "GTA V Fun Moments Gameplay",
            "channel": "GamingChannel",
            "description": "Playing with friends online.",
        }
    )
    await app.process_event(non_study_event)

    # Check database: Non-study event should NOT be inserted
    events = app.event_store.get_recent_events(limit=10)
    assert len(events) == 0

    # 2. Study video event -> should be observed & stored
    study_event = TesseractEvent(
        source="browser",
        event_type="youtube_watching",
        payload={
            "url": "https://www.youtube.com/watch?v=67890",
            "title": "Python Async Await Tutorial",
            "channel": "TechTutor",
            "description": "Understanding event loops and asynchronous programming.",
        }
    )
    await app.process_event(study_event)

    # Check database: Study event should be inserted and enriched with extracted topic
    events = app.event_store.get_recent_events(limit=10)
    assert len(events) == 1
    stored = events[0]
    assert stored["payload"].get("is_study_related") is True
    assert stored["payload"].get("extracted_topic") is not None

