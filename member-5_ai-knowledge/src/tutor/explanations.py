"""Concept explanation engine linking new topics to learner's existing mastered concepts."""

from typing import Dict, Any, Optional
from src.models.registry import registry
from src.knowledge.graph import knowledge_graph


async def generate_explanation(
    concept: str,
    user_level: str = "beginner",
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate first-principles explanation with analogies to already mastered concepts."""
    # Find learner's mastered concepts in the same domain
    snapshot = knowledge_graph.get_snapshot()
    mastered = [n.name for n in snapshot.nodes if n.status == "mastered"][:3]
    mastered_str = ", ".join(mastered) if mastered else "basic programming concepts"

    prompt = (
        f"You are an expert tutor. Explain '{concept}' to a {user_level} programmer.\n"
        f"Concepts they already understand well: [{mastered_str}].\n"
        f"Context of their current work: {context or 'General learning'}\n\n"
        f"Explain from first-principles using an intuitive analogy connected to what they already know. "
        f"Keep it concise, clear, and engaging."
    )

    result = await registry.complete(prompt=prompt, task_type="reason", max_tokens=500)
    return {
        "concept": concept,
        "explanation": result.content,
        "analogies_used": mastered,
        "model_used": result.model_name,
        "latency_ms": result.latency_ms,
    }
