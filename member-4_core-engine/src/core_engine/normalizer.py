"""
Event Normalization and Deduplication Engine for Tesseract Core Engine.
Normalizes heterogeneous sensor events into standard TesseractEvent schemas
and filters duplicate/flood events within a sliding time window.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import time
from collections import deque
from typing import Any

from .models import EventMetadata, TesseractEvent, generate_uuid, utc_now_iso

logger = logging.getLogger("tesseract.core_engine.normalizer")


class EventNormalizer:
    def __init__(self, dedup_window_ms: int = 2000, max_rate_per_second: int = 50):
        self.dedup_window_ms = dedup_window_ms
        self.max_rate_per_second = max_rate_per_second
        # Cache of (event_signature) -> timestamp_ms
        self._seen_signatures: dict[str, float] = {}
        # Rate limiter: source -> deque of timestamps
        self._rate_limiter: dict[str, deque[float]] = {}

    def normalize(self, raw_data: dict[str, Any]) -> TesseractEvent | None:
        """
        Normalize raw dictionary or sensor payload into a valid TesseractEvent.
        Returns None if rate-limited or deduplicated.
        """
        source = str(raw_data.get("source", "user")).lower()
        event_type = str(raw_data.get("event_type", "unknown"))
        timestamp = raw_data.get("timestamp") or utc_now_iso()
        payload = raw_data.get("payload", {})
        if not isinstance(payload, dict):
            payload = {"raw": payload}

        metadata_raw = raw_data.get("metadata", {})
        metadata = (
            EventMetadata.from_dict(metadata_raw)
            if isinstance(metadata_raw, dict)
            else EventMetadata()
        )
        event_id = raw_data.get("event_id")

        # Source-specific payload normalizations
        payload = self._normalize_payload(source, event_type, payload)

        event = TesseractEvent(
            event_id=event_id or generate_uuid(),
            source=source,  # type: ignore
            event_type=event_type,
            timestamp=timestamp,
            payload=payload,
            metadata=metadata,
        )

        # Check rate limiting
        if self._is_rate_limited(source):
            logger.warning(
                "Event dropped due to rate limiting: source=%s, type=%s", source, event_type
            )
            return None

        # Check deduplication
        if self._is_duplicate(event):
            logger.debug("Duplicate event dropped: source=%s, type=%s", source, event_type)
            return None

        return event

    def _normalize_payload(
        self, source: str, event_type: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Standardize keys across common sensor payload formats."""
        normalized = dict(payload)

        if source == "browser":
            # Normalize URLs and search queries
            if "url" in normalized:
                normalized["url"] = str(normalized["url"]).strip()
            if "query" in normalized:
                normalized["query"] = str(normalized["query"]).strip().lower()
            if "title" in normalized:
                normalized["title"] = str(normalized["title"]).strip()

        elif source in ("vscode", "vscode_sensor", "terminal", "editor"):
            # Normalize file paths and error messages
            if "file_path" in normalized:
                normalized["file_path"] = str(normalized["file_path"]).replace("\\", "/")
            if "error_message" in normalized:
                normalized["error_message"] = str(normalized["error_message"]).strip()
            if "exit_code" in normalized:
                with contextlib.suppress(ValueError, TypeError):
                    normalized["exit_code"] = int(normalized["exit_code"])

        elif source == "os":
            # Normalize application names
            if "app_name" in normalized:
                normalized["app_name"] = str(normalized["app_name"]).strip()

        return normalized

    def _compute_signature(self, event: TesseractEvent) -> str:
        """Compute stable hash signature for an event to check duplicates."""
        # Simplify payload to ignore transient keys like microsecond diffs
        sig_data = {
            "source": event.source,
            "event_type": event.event_type,
            "payload": event.payload,
        }
        raw_bytes = json.dumps(sig_data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(raw_bytes).hexdigest()

    def _is_duplicate(self, event: TesseractEvent) -> bool:
        """Check if an identical event occurred within the dedup window."""
        # Never deduplicate error events or terminal commands - repeated failures are primary friction signals!
        if "error" in event.event_type.lower() or "terminal" in event.event_type.lower():
            return False

        now_ms = time.time() * 1000.0
        sig = self._compute_signature(event)

        # Clean old entries
        cutoff = now_ms - self.dedup_window_ms
        self._seen_signatures = {k: v for k, v in self._seen_signatures.items() if v >= cutoff}

        if sig in self._seen_signatures:
            # Duplicate within window
            return True

        self._seen_signatures[sig] = now_ms
        return False

    def _is_rate_limited(self, source: str) -> bool:
        """Check if source exceeds max events per second."""
        now = time.time()
        if source not in self._rate_limiter:
            self._rate_limiter[source] = deque()

        q = self._rate_limiter[source]
        # Remove entries older than 1 second
        while q and q[0] <= now - 1.0:
            q.popleft()

        if len(q) >= self.max_rate_per_second:
            return True

        q.append(now)
        return False
