"""
Deterministic Rule-Based Intent Classifier for Tesseract Core Engine.
Categorizes user actions into Learning, Debugging, Working, Exploring, or Idle.
Provides deterministic scoring with optional fallback to AI Layer.
"""

from __future__ import annotations

import logging
from typing import Any

from .models import IntentType, TesseractEvent

logger = logging.getLogger("tesseract.core_engine.intent_classifier")


class IntentClassifier:
    def __init__(self, ai_client: Any | None = None):
        self.ai_client = ai_client

    def classify_event(self, event: TesseractEvent) -> tuple[IntentType, float, str]:
        """
        Classify a single event deterministically.
        Returns (intent, confidence, rationale).
        """
        source = event.source
        event_type = event.event_type.lower()
        payload = event.payload

        # 1. Debugging signals
        if (
            "error" in event_type
            or "diagnostic" in event_type
            or payload.get("exit_code", 0) not in (0, None)
            or payload.get("error_message")
            or "traceback" in str(payload).lower()
        ):
            return "debugging", 0.95, "Detected diagnostic error, non-zero exit code or traceback"

        if source == "browser":
            url = str(payload.get("url", "")).lower()
            query = str(payload.get("query", "")).lower()
            title = str(payload.get("title", "")).lower()

            # 2. Learning signals
            if "youtube.com" in url or "youtu.be" in url or "watch" in event_type or "youtube" in event_type:
                extracted_topic = payload.get("extracted_topic")
                is_study = payload.get("is_study_related")
                if is_study or extracted_topic:
                    return "learning", 0.95, f"Watching educational video on {extracted_topic or title}"
                if any(
                    k in title or k in query
                    for k in [
                        "tutorial",
                        "learn",
                        "course",
                        "how to",
                        "intro",
                        "explanation",
                        "lecture",
                    ]
                ):
                    return "learning", 0.90, "Watching educational video / tutorial"
                return "learning", 0.70, "Consuming media / video"


            if any(
                k in url or k in query or k in title
                for k in [
                    "docs.",
                    "documentation",
                    "tutorial",
                    "geeksforgeeks",
                    "w3schools",
                    "leetcode",
                    "hackerrank",
                ]
            ):
                return "learning", 0.85, "Browsing documentation / coding tutorial site"

            # 3. Debugging via search
            if any(
                k in query
                for k in [
                    "error",
                    "segmentation fault",
                    "segfault",
                    "exception",
                    "failed to",
                    "undefined reference",
                    "cannot find",
                    "stack overflow",
                ]
            ):
                return "debugging", 0.85, "Searching for bug fixes, errors, or troubleshooting"

            if "stackoverflow.com" in url:
                return "debugging", 0.85, "Reading StackOverflow troubleshooting thread"

            # 4. Exploring
            if "search" in event_type or "tab" in event_type:
                return "exploring", 0.60, "General web exploration / browsing"

        # 5. Working signals
        if source == "vscode" and any(
            k in event_type for k in ["file_edited", "saved", "typing", "build", "run", "execution"]
        ):
            if payload.get("exit_code") == 0 or not payload.get("error_message"):
                return "working", 0.85, "Active development and successful execution in IDE"
            return "debugging", 0.80, "Development cycle with build/execution issues"

        if source == "file" and any(k in event_type for k in ["created", "modified", "saved"]):
            return "working", 0.80, "Local file authored or modified"

        if source == "os":
            if "idle" in event_type:
                return "idle", 0.95, "OS user idle detected"
            return "working", 0.50, "General OS application usage"

        # Default fallback
        return "exploring", 0.40, "Ambiguous activity pattern"

    async def classify_intent_async(
        self, event: TesseractEvent, context_summary: dict[str, Any] | None = None
    ) -> tuple[IntentType, float, str]:
        """
        Classify intent with fallback to AI layer when confidence is low (< 0.5)
        and AI client is available.
        """
        intent, confidence, rationale = self.classify_event(event)

        if confidence < 0.5 and self.ai_client is not None:
            try:
                ai_result = await self.ai_client.classify_intent(
                    event_data=event.to_dict(),
                    context=context_summary or {},
                )
                if ai_result and "intent" in ai_result:
                    return (
                        ai_result["intent"],
                        float(ai_result.get("confidence", 0.8)),
                        "AI layer classification",
                    )
            except Exception as e:
                logger.warning(
                    "AI fallback classification failed: %s, using deterministic fallback", e
                )

        return intent, confidence, rationale
