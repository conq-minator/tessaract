"""
Stuck Detector and Friction Scoring Engine for Tesseract Core Engine.
Calculates deterministic friction scores based on behavioral signals:
repeated errors, execution attempts, search patterns, time without progress,
and tutorials consumed.
"""

from __future__ import annotations

import logging
from typing import Any

from .config import CoreConfig
from .models import FrictionLevel, FrictionScore, TesseractEvent

logger = logging.getLogger("tesseract.core_engine.stuck_detector")


class StuckDetector:
    def __init__(self, config: CoreConfig):
        self.config = config
        self.threshold_low = config.friction_threshold_low
        self.threshold_medium = config.friction_threshold_medium
        self.threshold_high = config.friction_threshold_high
        self.decay_rate = config.friction_decay_rate

        # Topic -> running friction state
        self._friction_state: dict[str, dict[str, Any]] = {}

    def get_friction_state(self, topic: str) -> dict[str, Any]:
        if topic not in self._friction_state:
            self._friction_state[topic] = {
                "error_count": 0,
                "last_error_signature": None,
                "repeated_errors": 0,
                "execution_attempts": 0,
                "search_count": 0,
                "time_without_progress_s": 0.0,
                "tutorials_opened": 0,
                "last_success_time": None,
                "last_event_time": None,
                "base_friction": 0.0,
            }
        return self._friction_state[topic]

    def update_with_event(self, event: TesseractEvent, topic: str = "general") -> FrictionScore:
        """Update friction state with a new event and compute updated score."""
        state = self.get_friction_state(topic)
        payload = event.payload
        source = event.source
        event_type = event.event_type.lower()

        # 1. Error detection
        is_error = False
        error_sig = None
        if (
            "error" in event_type
            or payload.get("exit_code", 0) not in (0, None)
            or payload.get("error_message")
        ):
            is_error = True
            error_sig = payload.get("error_message") or f"{event_type}_{payload.get('exit_code')}"

        if is_error:
            state["error_count"] += 1
            if error_sig and error_sig == state["last_error_signature"]:
                state["repeated_errors"] += 1
            else:
                state["last_error_signature"] = error_sig
        else:
            # Check for success (e.g. exit code 0 or successful build)
            if payload.get("exit_code") == 0 and "run" in event_type:
                # Reset error streaks on confirmed success
                state["repeated_errors"] = max(0, state["repeated_errors"] - 2)
                state["error_count"] = max(0, state["error_count"] - 2)

        # 2. Execution attempts
        if source == "vscode" and any(
            k in event_type
            for k in ["run", "execute", "build", "terminal_command", "diagnostic_error", "compile"]
        ):
            state["execution_attempts"] += 1

        # 3. Searches
        if source == "browser" and ("search" in event_type or "query" in payload):
            q = str(payload.get("query", "")).lower()
            if any(
                k in q
                for k in [
                    "error",
                    "fix",
                    "issue",
                    "bug",
                    "segfault",
                    "pointer",
                    "why does",
                    "cannot",
                ]
            ):
                state["search_count"] += 1

        # 4. Tutorials
        if source == "browser" and (
            "youtube" in event_type
            or "youtube.com" in str(payload.get("url", ""))
            or "tutorial" in str(payload.get("title", "")).lower()
        ):
            state["tutorials_opened"] += 1

        # 5. Time without progress estimation
        time_spent_add = 180.0  # seconds per friction interaction cycle
        if is_error or ("search" in event_type) or ("youtube" in event_type):
            state["time_without_progress_s"] += time_spent_add

        return self.compute_friction_score(topic)

    def decay_friction(self, topic: str) -> FrictionScore:
        """Apply passive time-based decay to running friction."""
        state = self.get_friction_state(topic)
        state["repeated_errors"] = max(0, int(state["repeated_errors"] * self.decay_rate))
        state["search_count"] = max(0, int(state["search_count"] * self.decay_rate))
        state["execution_attempts"] = max(0, int(state["execution_attempts"] * self.decay_rate))
        state["time_without_progress_s"] = max(
            0.0, state["time_without_progress_s"] * self.decay_rate
        )
        return self.compute_friction_score(topic)

    def reset_topic(self, topic: str) -> None:
        """Reset friction on problem resolution."""
        if topic in self._friction_state:
            del self._friction_state[topic]

    def compute_friction_score(self, topic: str) -> FrictionScore:
        """Calculate weighted friction score between 0.0 and 1.0."""
        state = self.get_friction_state(topic)

        # Configurable weights
        w_rep_errors = 0.30
        w_exec = 0.20
        w_searches = 0.15
        w_time = 0.25
        w_tutorials = 0.10

        # Normalization ceilings
        max_rep_errors = 5.0
        max_exec = 8.0
        max_searches = 4.0
        max_time_s = 1800.0  # 30 mins
        max_tutorials = 1.5

        c_rep = min(1.0, state["repeated_errors"] / max_rep_errors) * w_rep_errors
        c_exec = min(1.0, state["execution_attempts"] / max_exec) * w_exec
        c_search = min(1.0, state["search_count"] / max_searches) * w_searches
        c_time = min(1.0, state["time_without_progress_s"] / max_time_s) * w_time
        c_tut = min(1.0, state["tutorials_opened"] / max_tutorials) * w_tutorials

        total_score = round(min(1.0, c_rep + c_exec + c_search + c_time + c_tut), 2)

        # Determine level
        if total_score >= self.threshold_high:
            level: FrictionLevel = "high"
        elif total_score >= self.threshold_medium:
            level = "medium"
        else:
            level = "low"

        signals = {
            "repeated_errors": {
                "count": state["repeated_errors"],
                "weight": w_rep_errors,
                "contribution": round(c_rep, 2),
            },
            "execution_attempts": {
                "count": state["execution_attempts"],
                "weight": w_exec,
                "contribution": round(c_exec, 2),
            },
            "search_count": {
                "count": state["search_count"],
                "weight": w_searches,
                "contribution": round(c_search, 2),
            },
            "time_without_progress_s": {
                "value": round(state["time_without_progress_s"], 1),
                "weight": w_time,
                "contribution": round(c_time, 2),
            },
            "tutorials_opened": {
                "count": state["tutorials_opened"],
                "weight": w_tutorials,
                "contribution": round(c_tut, 2),
            },
        }

        return FrictionScore(
            score=total_score,
            level=level,
            signals=signals,
            threshold_low=self.threshold_low,
            threshold_medium=self.threshold_medium,
            threshold_high=self.threshold_high,
        )
