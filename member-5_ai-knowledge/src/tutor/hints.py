"""Progressive pedagogical assistance engine generating Levels 1 through 5 assistance."""

import asyncio
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

    error_context = f"\nLearner's current error / situation: {context}\n" if context else ""

    prompts = {
        1: (
            f"You are an expert programming tutor helping a learner stuck on '{topic}' (Friction: {friction_score:.2f}). {gap_context}"
            f"{error_context}"
            f"Provide a LEVEL 1 HINT: Directly point out what part of their code or operation to inspect based on the error and code above. "
            f"CRITICAL RULES:\n"
            f"- NEVER ask the user questions like 'what error are you seeing?' or 'can you provide more info?'.\n"
            f"- DO NOT provide the full solution code.\n"
            f"- Give a direct, insightful pedagogical hint in 1-2 concise sentences."
        ),
        2: (
            f"You are an expert programming tutor helping a learner with '{topic}'. {gap_context}"
            f"{error_context}"
            f"Provide a LEVEL 2 CONCEPT EXPLANATION: Explain the underlying mental model simply in 1-2 paragraphs using a vivid real-world analogy. Clearly explain why this specific error happens and how the language behaves under the hood."
        ),
        3: (
            f"You are an expert programming tutor helping a learner with '{topic}'. {gap_context}"
            f"{error_context}"
            f"Provide a LEVEL 3 DETAILED BREAKDOWN: Break down step-by-step what happens in memory, types, and control flow when this error triggers, showing the before-and-after fix."
        ),
        4: (
            f"You are an expert programming tutor helping a learner with '{topic}'. {gap_context}"
            f"{error_context}"
            f"Provide a LEVEL 4 PRACTICE PROBLEM on '{topic}' to test understanding. Present a single bite-sized scenario or puzzle."
        ),
        5: (
            f"You are an expert programming tutor helping a learner with '{topic}'. {gap_context}"
            f"{error_context}"
            f"Provide the complete, correct solution, annotated with clear comments explaining why each line works."
        ),
    }

    prompt = prompts[level]
    content = ""
    model_name = "smollm2:1.7b"
    latency_ms = 0.0

    try:
        max_toks = 150 if level <= 2 else 300
        result = await asyncio.wait_for(
            registry.complete(prompt=prompt, task_type="reason", max_tokens=max_toks),
            timeout=5.0
        )
        content = result.content
        model_name = result.model_name
        latency_ms = result.latency_ms

        # If model returned a generic non-hint asking the user questions, fallback to smart rule
        c_low = (content or "").lower()
        if not content or "what is the exact error" in c_low or "what error are you seeing" in c_low or "can you provide" in c_low:
            raise ValueError("Model gave generic query instead of hint")
    except Exception as e:
        # Context-aware smart pedagogical fallback
        c_lower = str(context or "").lower()
        if "typeerror" in c_lower and "concatenate str" in c_lower:
            content = "In Python, '+' cannot combine a string with an integer directly. Check the initial type of your accumulator and ensure both operands have matching types."
        elif "typeerror" in c_lower:
            content = f"A type mismatch occurred in {topic}. Check the data types of variables being operated on or passed to functions."
        elif "indexerror" in c_lower:
            content = "Lists in Python are 0-indexed and run up to len - 1. Check whether your loop range or index reaches beyond the last element."
        elif "keyerror" in c_lower:
            content = "The dictionary key does not exist. Check if the key is present using 'key in dict' or safely retrieve it with 'dict.get(key, default)'."
        elif "recursionerror" in c_lower:
            content = "The recursion depth limit was exceeded. Verify that your recursive function has a reachable base case that stops execution."
        elif "syntaxerror" in c_lower:
            content = f"A syntax error was detected in {topic}. Check matching colons, brackets, and keyword placement on the indicated line."
        elif "pointer" in c_lower or "segfault" in c_lower or "segmentation" in c_lower:
            content = "A segmentation fault occurred. Ensure pointers are allocated with valid memory addresses before dereferencing with '*'."
        else:
            fallbacks = {
                "python": "In Python, verify your syntax, indentation, and ensure variable types match expected operations.",
                "javascript": "In JavaScript, check for undefined variables, missing async/await, or scope boundaries.",
                "c": "In C, ensure pointers point to allocated memory and array indexes stay within bounds.",
                "general": "Double check syntax error line markers and verify that matching brackets, quotes, and keywords are intact."
            }
            content = fallbacks.get(topic.lower(), f"Check your {topic} error details and variable types.")
        model_name = "smart-rules"

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
        "content": content,
        "hint": content,
        "identified_gaps": gap_names,
        "model_used": model_name,
        "latency_ms": latency_ms,
    }
