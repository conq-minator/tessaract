"""Adaptive learning roadmap builder based on knowledge graph state and study time constraints."""

import json
from typing import Dict, Any, List, Optional
from src.models.registry import registry
from src.knowledge.graph import knowledge_graph


async def generate_adaptive_roadmap(
    subject: str,
    target_goal: Optional[str] = None,
    available_time_per_day: str = "1_hour_per_day",  # '30_min_per_day', '1_hour_per_day', '2_hours_per_day', 'weekend_only'
) -> Dict[str, Any]:
    """
    Generate or adapt a learning roadmap for a subject.
    Considers the learner's current knowledge graph (skipping mastered topics, prioritizing weak prerequisites).
    """
    snapshot = knowledge_graph.get_snapshot()
    domain_nodes = [n for n in snapshot.nodes if subject.lower() in n.domain.lower()]

    mastered = [n.name for n in domain_nodes if n.status == "mastered"]
    weak = [n.name for n in domain_nodes if n.status == "weak"]
    developing = [n.name for n in domain_nodes if n.status == "developing"]

    prompt = (
        f"You are a personalized curriculum designer. Create an adaptive study roadmap for '{subject}'.\n"
        f"Goal: {target_goal or 'Complete mastery'}\n"
        f"Study pacing: {available_time_per_day.replace('_', ' ')}\n"
        f"Current Knowledge State:\n"
        f"- Already Mastered (SKIP OR REVIEW FAST): {mastered}\n"
        f"- Weak / Stuck Areas (PRIORITIZE): {weak}\n"
        f"- Developing: {developing}\n\n"
        f"Output JSON with this schema:\n"
        f"{{\n"
        f"  \"subject\": \"{subject}\",\n"
        f"  \"estimated_weeks\": 4,\n"
        f"  \"pacing\": \"{available_time_per_day}\",\n"
        f"  \"milestones\": [\n"
        f"    {{\"phase\": 1, \"title\": \"...\", \"focus\": \"...\", \"estimated_hours\": 5, \"status\": \"pending\"}}\n"
        f"  ]\n"
        f"}}"
    )

    result = await registry.complete(prompt=prompt, task_type="classify", max_tokens=400)
    raw = result.content.strip()

    roadmap_data = None
    try:
        if "{" in raw and "}" in raw:
            json_str = raw[raw.find("{"):raw.rfind("}") + 1]
            roadmap_data = json.loads(json_str)
    except Exception:
        pass

    if not roadmap_data:
        # Fallback structured roadmap
        roadmap_data = {
            "subject": subject,
            "estimated_weeks": 4,
            "pacing": available_time_per_day,
            "milestones": [
                {
                    "phase": 1,
                    "title": f"Foundation & Weak Points: {', '.join(weak[:2]) if weak else 'Core syntax'}",
                    "focus": "Review missing prerequisites and strengthen mental models",
                    "estimated_hours": 4,
                    "status": "in_progress",
                },
                {
                    "phase": 2,
                    "title": f"Intermediate Application in {subject}",
                    "focus": "Building small programs and handling edge cases",
                    "estimated_hours": 6,
                    "status": "pending",
                },
                {
                    "phase": 3,
                    "title": "Advanced Projects & Problem Solving",
                    "focus": "End-to-end implementation and optimization",
                    "estimated_hours": 8,
                    "status": "pending",
                },
            ],
        }

    return {
        "roadmap": roadmap_data,
        "model_used": result.model_name,
        "latency_ms": result.latency_ms,
    }
