"""
Test Episode Grouper.
"""

from pathlib import Path

from core_engine.config import CoreConfig
from core_engine.episode_grouper import EpisodeGrouper
from core_engine.event_store import EventStore
from core_engine.models import TesseractEvent
from core_engine.stuck_detector import StuckDetector


def test_episode_grouper_flow(tmp_path: Path):
    db_file = tmp_path / "test_episodes.db"
    store = EventStore(db_file)
    config = CoreConfig()
    detector = StuckDetector(config)

    completed_episodes = []

    def on_complete(ep):
        completed_episodes.append(ep)

    grouper = EpisodeGrouper(
        event_store=store,
        stuck_detector=detector,
        gap_timeout_s=60,
        on_episode_completed=on_complete,
    )

    # 1. Error event in VS Code
    e1 = TesseractEvent(
        source="vscode",
        event_type="build_run",
        payload={"exit_code": 1, "error_message": "Segmentation fault"},
    )
    ep1 = grouper.process_event(
        e1, session_id="s1", inferred_intent="debugging", inferred_topic="pointers"
    )
    assert ep1.outcome == "ongoing"
    assert ep1.signals["error_count"] == 1

    # 2. Browser Search
    e2 = TesseractEvent(
        source="browser",
        event_type="search",
        payload={"query": "segmentation fault pointers"},
    )
    ep2 = grouper.process_event(
        e2, session_id="s1", inferred_intent="debugging", inferred_topic="pointers"
    )
    assert ep2.signals["search_count"] == 1

    # 3. Successful run -> Resolves episode
    e3 = TesseractEvent(
        source="vscode",
        event_type="build_run",
        payload={"exit_code": 0, "output": "Success"},
    )
    ep3 = grouper.process_event(
        e3, session_id="s1", inferred_intent="working", inferred_topic="pointers"
    )
    assert ep3.outcome == "resolved"
    assert len(completed_episodes) == 1
    assert completed_episodes[0].outcome == "resolved"
