"""Epistemic confidence scoring algorithms and temporal decay."""

from datetime import datetime, timezone
from typing import Dict

# Standard evidence weights
SIGNAL_WEIGHTS: Dict[str, float] = {
    "error_resolved": 0.08,
    "execution_success": 0.05,
    "tutorial_watched": 0.04,
    "practice_completed": 0.12,
    "search_performed": 0.02,
    "repeated_error": -0.07,
    "syntax_error": -0.03,
    "abrupt_close": -0.04,
}


def calculate_status(confidence: float) -> str:
    """Categorize confidence score into human-readable epistemic status."""
    if confidence < 0.35:
        return "weak"
    elif confidence < 0.65:
        return "developing"
    elif confidence < 0.85:
        return "good"
    else:
        return "mastered"


def calculate_new_confidence(
    current_confidence: float,
    evidence_type: str,
    custom_delta: float = 0.0,
    evidence_count: int = 1,
) -> float:
    """
    Calculate updated confidence score given incoming behavioral evidence.
    Diminishing returns kick in as confidence approaches 1.0 or 0.0.
    """
    base_delta = SIGNAL_WEIGHTS.get(evidence_type, custom_delta)
    if custom_delta != 0.0:
        delta = custom_delta
    else:
        delta = base_delta

    # Diminishing returns scaling
    if delta > 0:
        # Harder to gain confidence as you get closer to 1.0
        scaled_delta = delta * (1.0 - (current_confidence * 0.5))
    else:
        # Mistakes when already weak don't drop score to zero instantly
        scaled_delta = delta * (current_confidence + 0.2)

    new_conf = current_confidence + scaled_delta
    return max(0.0, min(1.0, round(new_conf, 4)))


def apply_temporal_decay(
    confidence: float,
    last_updated_iso: str,
    decay_rate_per_day: float = 0.005,
    grace_period_days: int = 7,
) -> float:
    """
    Apply gentle forgetting/decay curve if no activity occurred for > grace_period_days.
    Confidence never decays below a baseline floor of 0.20 for learned concepts.
    """
    try:
        last_dt = datetime.fromisoformat(last_updated_iso.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_passed = (now - last_dt).total_seconds() / 86400.0

        if days_passed <= grace_period_days:
            return confidence

        inactive_days = days_passed - grace_period_days
        decay_amount = inactive_days * decay_rate_per_day
        decayed = max(0.20, confidence - decay_amount)
        return round(decayed, 4)
    except Exception:
        return confidence
