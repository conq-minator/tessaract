"""
Test Stuck Detector and Friction Scorer.
"""

from core_engine.config import CoreConfig
from core_engine.models import TesseractEvent
from core_engine.stuck_detector import StuckDetector


def test_stuck_detector_scoring():
    config = CoreConfig(
        friction_threshold_low=0.3,
        friction_threshold_medium=0.5,
        friction_threshold_high=0.7,
    )
    detector = StuckDetector(config)

    # Initial score should be 0
    score0 = detector.compute_friction_score("pointers")
    assert score0.score == 0.0
    assert score0.level == "low"

    # Multiple repeated errors + searches should increase friction
    for _ in range(4):
        detector.update_with_event(
            TesseractEvent(
                source="vscode",
                event_type="diagnostic_error",
                payload={"error_message": "Segmentation fault"},
            ),
            topic="pointers",
        )

    for _ in range(3):
        detector.update_with_event(
            TesseractEvent(
                source="browser",
                event_type="search",
                payload={"query": "segmentation fault c fix"},
            ),
            topic="pointers",
        )

    # Open tutorial
    detector.update_with_event(
        TesseractEvent(
            source="browser",
            event_type="youtube_watch",
            payload={"url": "https://youtube.com/watch?v=123", "title": "Pointers tutorial"},
        ),
        topic="pointers",
    )

    final_score = detector.compute_friction_score("pointers")
    assert final_score.score >= 0.5
    assert final_score.level in ("medium", "high")


def test_friction_decay():
    config = CoreConfig(friction_decay_rate=0.5)
    detector = StuckDetector(config)

    # Add error
    detector.update_with_event(
        TesseractEvent(
            source="vscode",
            event_type="diagnostic_error",
            payload={"error_message": "Segmentation fault"},
        ),
        topic="pointers",
    )
    score1 = detector.compute_friction_score("pointers")

    # Apply decay
    score2 = detector.decay_friction("pointers")
    assert score2.score <= score1.score
