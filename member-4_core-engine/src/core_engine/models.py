"""
Data models and schemas for Tesseract Core Engine.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat()


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


SourceType = Literal["browser", "vscode", "os", "file", "multimodal", "user"]
PrivacyLevel = Literal["local_only", "abstractable", "cloud_safe"]
IntentType = Literal["learning", "working", "debugging", "exploring", "idle"]
EpisodeOutcome = Literal["resolved", "ongoing", "abandoned"]
FrictionLevel = Literal["low", "medium", "high"]


@dataclass
class EventMetadata:
    session_id: str | None = None
    confidence: float = 1.0
    privacy_level: PrivacyLevel = "local_only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> EventMetadata:
        if not data:
            return cls()
        return cls(
            session_id=data.get("session_id"),
            confidence=float(data.get("confidence", 1.0)),
            privacy_level=data.get("privacy_level", "local_only"),
        )


@dataclass
class TesseractEvent:
    event_type: str
    source: SourceType
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=generate_uuid)
    timestamp: str = field(default_factory=utc_now_iso)
    metadata: EventMetadata = field(default_factory=EventMetadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "source": self.source,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "metadata": (
                self.metadata.to_dict()
                if isinstance(self.metadata, EventMetadata)
                else self.metadata
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TesseractEvent:
        meta_raw = data.get("metadata", {})
        metadata = (
            EventMetadata.from_dict(meta_raw) if isinstance(meta_raw, dict) else EventMetadata()
        )
        return cls(
            event_id=data.get("event_id", generate_uuid()),
            source=data.get("source", "user"),
            event_type=data.get("event_type", "unknown"),
            timestamp=data.get("timestamp", utc_now_iso()),
            payload=data.get("payload", {}),
            metadata=metadata,
        )


@dataclass
class Session:
    session_id: str = field(default_factory=generate_uuid)
    start_time: str = field(default_factory=utc_now_iso)
    end_time: str | None = None
    is_active: bool = True
    events_count: int = 0
    sources: list[str] = field(default_factory=list)
    primary_intent: IntentType = "working"
    topics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Session:
        return cls(
            session_id=data["session_id"],
            start_time=data["start_time"],
            end_time=data.get("end_time"),
            is_active=data.get("is_active", True),
            events_count=data.get("events_count", 0),
            sources=list(data.get("sources", [])),
            primary_intent=data.get("primary_intent", "working"),
            topics=list(data.get("topics", [])),
        )


@dataclass
class Episode:
    episode_id: str = field(default_factory=generate_uuid)
    session_ids: list[str] = field(default_factory=list)
    start_time: str = field(default_factory=utc_now_iso)
    end_time: str | None = None
    topic: str = "general"
    intent: IntentType = "learning"
    outcome: EpisodeOutcome = "ongoing"
    events_count: int = 0
    friction_score: float = 0.0
    signals: dict[str, Any] = field(
        default_factory=lambda: {
            "error_count": 0,
            "execution_attempts": 0,
            "search_count": 0,
            "time_spent_s": 0,
            "tutorials_opened": 0,
        }
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Episode:
        return cls(
            episode_id=data["episode_id"],
            session_ids=list(data.get("session_ids", [])),
            start_time=data["start_time"],
            end_time=data.get("end_time"),
            topic=data.get("topic", "general"),
            intent=data.get("intent", "learning"),
            outcome=data.get("outcome", "ongoing"),
            events_count=data.get("events_count", 0),
            friction_score=float(data.get("friction_score", 0.0)),
            signals=dict(data.get("signals", {})),
        )


@dataclass
class FrictionSignal:
    count: int | None = None
    value: float | None = None
    weight: float = 0.0
    contribution: float = 0.0


@dataclass
class FrictionScore:
    score: float = 0.0
    level: FrictionLevel = "low"
    signals: dict[str, dict[str, Any]] = field(default_factory=dict)
    threshold_low: float = 0.3
    threshold_medium: float = 0.5
    threshold_high: float = 0.7

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AlertMessage:
    alert_type: Literal[
        "stuck_detected", "episode_completed", "context_changed", "milestone_reached"
    ]
    payload: dict[str, Any]
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_type": self.alert_type,
            "type": self.alert_type,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }


@dataclass
class ContextState:
    topic: str = "general"
    intent: str = "working"
    active_tools: list[str] = field(default_factory=list)
    friction_level: FrictionLevel = "low"
    active_session_id: str | None = None
    active_episode_id: str | None = None
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
