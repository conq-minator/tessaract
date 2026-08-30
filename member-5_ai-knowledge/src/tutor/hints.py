"""Progressive pedagogical assistance engine generating Levels 1 through 5 assistance."""

from typing import Dict, Any, Optional
from src.models.registry import registry
from src.knowledge.graph import knowledge_graph


async def generate_progressive_assistance(
    topic: str,
    level: int = 1,
    context: Optional[str] = None,
    friction_score: float = 0.5,
) -> Dict[str, Any]:
    """
    Generate progressive assistance for a user struggling with a topic.
    Levels:
      1 -> Minimal hint pointing to first principles
      2 -> Concept explanation with analogies
      3 -> Detailed breakdown with code/step examples
      4 -> Interactive practice question testing the weak concept
      5 -> Complete guided solution
    """
    level = max(1, min(5, level))

    # Retrieve relevant skill and prerequisite gaps from the Knowledge Graph
    gaps = knowledge_graph.find_prerequisite_gaps(topic)
    gap_names = [g.name for g in gaps[:2]] if gaps else []
    gap_context = f"Missing prerequisites identified: {', '.join(gap_names)}. " if gap_names else ""

    prompts = {
        1: (
            f"You are a progressive learning tutor. The user is stuck on '{topic}' (Friction: {friction_score:.2f}). {gap_context}"
            f"Provide a LEVEL 1 HINT: Give a short, thought-provoking question or nudge toward first principles. "
            f"DO NOT give the answer or write code. Max 2 sentences."
        ),
        2: (
            f"You are a progressive learning tutor. The user needs a LEVEL 2 CONCEPT EXPLANATION for '{topic}'. {gap_context}"
            f"Explain the mental model simply in 1-2 paragraphs. Use a concrete real-world analogy. No copy-paste solutions."
        ),
        3: (
            f"You are a progressive learning tutor. The user needs a LEVEL 3 DETAILED BREAKDOWN for '{topic}'. {gap_context}"
            f"Break the concept down step-by-step. Show what is happening under the hood (e.g. memory addresses, call stack, execution flow)."
        ),
        4: (
            f"You are a progressive learning tutor. The user needs a LEVEL 4 PRACTICE PROBLEM on '{topic}' to test understanding. {gap_context}"
            f"Present a single, bite-sized practice scenario or puzzle. Ask them what the output or bug is, without giving away the answer."
        ),
        5: (
            f"You are a progressive learning tutor. The user has reached LEVEL 5 FULL SOLUTION for '{topic}'. {gap_context}"
            f"Context: {context or 'None provided'}\n"
            f"Provide the complete, correct solution, annotated with clear comments explaining why each line works."
        ),
    }

    prompt = prompts[level]
    result = await registry.complete(prompt=prompt, task_type="reason", max_tokens=600)

    level_names = {
        1: "Hint",
        2: "Concept Explanation",
        3: "Detailed Breakdown",
        4: "Practice Problem",
        5: "Full Guided Solution",
    }

    return {
        "level": level,
        "level_name": level_names[level],
        "topic": topic,
        "content": result.content,
        "identified_gaps": gap_names,
        "model_used": result.model_name,
        "latency_ms": result.latency_ms,
    }
