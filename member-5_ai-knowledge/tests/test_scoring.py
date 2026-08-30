"""Unit tests for epistemic confidence scoring and decay."""

import pytest
from src.knowledge.scoring import (
    calculate_new_confidence,
    calculate_status,
    apply_temporal_decay,
)


def test_calculate_status():
    assert calculate_status(0.20) == "weak"
    assert calculate_status(0.50) == "developing"
    assert calculate_status(0.75) == "good"
    assert calculate_status(0.92) == "mastered"


def test_confidence_increase_on_success():
    initial = 0.50
    updated = calculate_new_confidence(initial, evidence_type="error_resolved")
    assert updated > initial
    assert updated <= 1.0


def test_confidence_decrease_on_repeated_error():
    initial = 0.50
    updated = calculate_new_confidence(initial, evidence_type="repeated_error")
    assert updated < initial
    assert updated >= 0.0


def test_temporal_decay():
    # Fresh update -> no decay
    fresh_iso = "2026-08-30T10:00:00+00:00"
    assert apply_temporal_decay(0.80, fresh_iso) == 0.80

    # Old update (30 days ago) -> decay capped at floor
    old_iso = "2026-01-01T00:00:00+00:00"
    decayed = apply_temporal_decay(0.80, old_iso)
    assert decayed < 0.80
    assert decayed >= 0.20
