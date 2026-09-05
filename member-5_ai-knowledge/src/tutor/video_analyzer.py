"""
Intelligent Video Topic Extractor and Study Relevance Classifier for Tesseract AI Layer.
Extracts the conceptual topic and determines if a media/video source is study/educational
or general entertainment.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict
from src.models.registry import registry
from src.models.base import VideoAnalysisResult

logger = logging.getLogger("tesseract.ai_knowledge.video_analyzer")

VIDEO_CLASSIFICATION_PROMPT = """
You are an intelligent educational filter for Tesseract, an AI programming tutor and study assistant.
Analyze the following video metadata and extract the primary conceptual topic. Then decide if this video is study/educational or non-study entertainment.

Study-related includes: programming, computer science, software engineering, algorithms, mathematics, physics, science, academic courses, technical tutorials, electronics, machine learning, and structured educational lectures.
Non-study includes: gaming gameplay/streaming, music videos, movie trailers, comedy skits, vlogs, gossip, reactions, entertainment news, and sports.

Metadata:
- Title: {title}
- Channel: {channel}
- Description: {description}

You MUST reply with ONLY a single valid JSON object in this exact schema (no markdown, no other text):
{{
  "topic": "<concise name of the primary subject or concept being taught>",
  "is_study_related": true or false,
  "domain": "<computer_science | mathematics | science | academic | general_study | entertainment | gaming | leisure>",
  "confidence": 0.95,
  "rationale": "<brief 1-sentence reason>"
}}
"""

# High-confidence heuristics for fallback
STUDY_KEYWORDS = [
    "tutorial", "course", "lecture", "learn", "how to", "explained", "crash course",
    "python", "javascript", "c++", "rust", "algorithm", "data structure", "compiler",
    "pointer", "database", "sql", "linux", "git", "web dev", "frontend", "backend",
    "machine learning", "deep learning", "calculus", "linear algebra", "physics",
    "leetcode", "neetcode", "cs50", "freecodecamp", "mit opencourseware"
]

NON_STUDY_KEYWORDS = [
    "gameplay", "speedrun", "walkthrough game", "trailer", "official music video",
    "vlog", "funny moments", "prank", "reaction", "highlights", "meme", "tiktok"
]


def heuristic_video_classification(title: str, channel: str = "", description: str = "") -> VideoAnalysisResult:
    """Fast deterministic heuristic fallback if AI model is unreachable."""
    combined = f"{title} {channel} {description}".lower()

    # Check non-study first
    if any(k in combined for k in NON_STUDY_KEYWORDS):
        return VideoAnalysisResult(
            topic=title.strip() or "Entertainment Media",
            is_study_related=False,
            domain="entertainment",
            confidence=0.85,
            rationale="Contains entertainment/gaming keywords",
        )

    # Check study keywords
    matched_kw = [k for k in STUDY_KEYWORDS if k in combined]
    if matched_kw:
        matched_str = matched_kw[0].title()
        return VideoAnalysisResult(
            topic=f"{matched_str} Study" if len(matched_kw) == 1 else title.strip(),
            is_study_related=True,
            domain="computer_science" if any(c in combined for c in ["python", "c++", "rust", "algorithm", "pointer", "sql", "code"]) else "general_study",
            confidence=0.88,
            rationale=f"Matched educational indicators: {', '.join(matched_kw[:3])}",
        )

    # Default to non-study when ambiguous
    return VideoAnalysisResult(
        topic=title.strip() or "General Media",
        is_study_related=False,
        domain="general",
        confidence=0.60,
        rationale="Ambiguous content without explicit educational signals",
    )


async def analyze_video_topic(
    title: str,
    channel: str = "",
    description: str = "",
) -> Dict[str, Any]:
    """
    Extract video topic and determine study relevance using local SLM with heuristic fallback.
    """
    if not title and not channel:
        return VideoAnalysisResult().model_dump()

    prompt = VIDEO_CLASSIFICATION_PROMPT.format(
        title=title or "Untitled",
        channel=channel or "Unknown Channel",
        description=description[:300] if description else "None provided",
    )

    try:
        completion = await registry.complete(
            prompt=prompt,
            task_type="reason",
            max_tokens=180,
            temperature=0.1,
        )

        raw_text = completion.text.strip()
        # Clean potential markdown formatting
        cleaned_json = raw_text
        if "```" in raw_text:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
            if match:
                cleaned_json = match.group(1)
            else:
                cleaned_json = raw_text.replace("```json", "").replace("```", "").strip()

        parsed = json.loads(cleaned_json)
        result = VideoAnalysisResult(
            topic=str(parsed.get("topic") or title).strip(),
            is_study_related=bool(parsed.get("is_study_related", False)),
            domain=str(parsed.get("domain", "general")),
            confidence=float(parsed.get("confidence", 0.85)),
            rationale=str(parsed.get("rationale", "AI model evaluation")),
        )
        return result.model_dump()

    except Exception as e:
        logger.debug("AI video analysis fallback invoked (%s)", e)
        fallback = heuristic_video_classification(title, channel, description)
        return fallback.model_dump()
