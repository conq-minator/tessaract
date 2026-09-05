"""Tests for AI Video Topic Extraction and Study Relevance Filter."""

import pytest
from src.models.registry import registry
from src.tutor.video_analyzer import analyze_video_topic, heuristic_video_classification


@pytest.mark.asyncio
async def test_video_analyzer_study_content():
    registry.set_mock_mode(True)
    result = await analyze_video_topic(
        title="Python Async Await Tutorial for Beginners",
        channel="TechWithTim",
        description="Learn how to write asynchronous concurrency in Python with asyncio."
    )
    assert result["is_study_related"] is True
    assert "topic" in result
    assert result["confidence"] > 0.5


@pytest.mark.asyncio
async def test_video_analyzer_non_study_content():
    registry.set_mock_mode(True)
    result = await analyze_video_topic(
        title="Minecraft Speedrun 1.20 World Record",
        channel="GamingLegend",
        description="Insane Nether fortress blaze rod luck and ender dragon fight."
    )
    assert result["is_study_related"] is False
    assert result["domain"] in ("entertainment", "gaming", "general")


def test_heuristic_fallback_educational():
    res = heuristic_video_classification(
        title="MIT 6.006 Introduction to Algorithms Lecture 1",
        channel="MIT OpenCourseWare",
        description="Introduction to asymptotic notation and sorting algorithms."
    )
    assert res.is_study_related is True
    assert res.domain in ("computer_science", "general_study")


def test_heuristic_fallback_entertainment():
    res = heuristic_video_classification(
        title="Official Music Video 4K",
        channel="TopHitsMusic",
        description="Stream the new single on all platforms now."
    )
    assert res.is_study_related is False
    assert res.domain == "entertainment"
