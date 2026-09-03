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

    import asyncio
    try:
        result = await asyncio.wait_for(
            registry.complete(prompt=prompt, task_type="reason", max_tokens=250),
            timeout=5.0
        )
        content = result.content
        model_used = result.model_name
        latency_ms = result.latency_ms
    except Exception:
        if "python" in concept.lower() or "loop" in concept.lower():
            content = (
                "### Understanding Python `for` Loops\n\n"
                "In Python, a `for` loop iterates directly over items in a sequence (like a list, string, or range):\n\n"
                "```python\n"
                "# Correct Syntax:\n"
                "items = [1, 2, 3, 4]\n"
                "for num in items:\n"
                "    print(num)\n"
                "```\n\n"
                "**Common Pitfall**: In some languages, keywords like `in` or type declarations go before the variable name. "
                "In Python, always write `for <variable> in <iterable>:` without extra keywords before the variable name."
            )
        elif "pointer" in concept.lower():
            content = (
                "### Understanding Pointers\n\n"
                "A pointer is a variable that stores the memory address of another value rather than the value itself."
            )
        else:
            content = f"Explanation of {concept}: Review first principles and underlying data flow."
        model_used = "fast-rules"
        latency_ms = 0.0

    return {
        "concept": concept,
        "explanation": content,
        "analogies_used": mastered,
        "model_used": model_used,
        "latency_ms": latency_ms,
    }
