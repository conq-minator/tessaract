"""
Test Intent Classifier.
"""

from core_engine.intent_classifier import IntentClassifier
from core_engine.models import TesseractEvent


def test_intent_classifier_debugging():
    classifier = IntentClassifier()

    event = TesseractEvent(
        source="vscode",
        event_type="build_run",
        payload={"exit_code": 1, "error_message": "Segmentation fault"},
    )
    intent, conf, _rat = classifier.classify_event(event)
    assert intent == "debugging"
    assert conf >= 0.8


def test_intent_classifier_learning():
    classifier = IntentClassifier()

    event = TesseractEvent(
        source="browser",
        event_type="youtube_watch",
        payload={"url": "https://youtube.com/watch?v=123", "title": "C Programming Tutorial"},
    )
    intent, conf, _rat = classifier.classify_event(event)
    assert intent == "learning"
    assert conf >= 0.8


def test_intent_classifier_working():
    classifier = IntentClassifier()

    event = TesseractEvent(
        source="vscode",
        event_type="file_edited",
        payload={"file_path": "src/main.c", "lines_changed": 10},
    )
    intent, conf, _rat = classifier.classify_event(event)
    assert intent == "working"
    assert conf >= 0.8
