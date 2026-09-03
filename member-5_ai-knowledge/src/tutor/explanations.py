"""Concept explanation engine linking new topics to learner's existing mastered concepts."""

from typing import Dict, Any, Optional, List
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


async def answer_user_question(
    question: str,
    topic: str,
    error: str = "",
    code: str = "",
    file_path: str = ""
) -> Dict[str, Any]:
    """Answer a user's prompt directly in context of their code and error."""
    prompt = (
        f"You are an encouraging and expert programming tutor.\n"
        f"Topic: {topic}\n"
        f"File: {file_path or 'unknown'}\n"
        f"Runtime Error: {error or 'None specified'}\n"
        f"Code Snippet:\n```\n{code or 'No snippet provided'}\n```\n\n"
        f"User's Question: \"{question}\"\n\n"
        f"Instructions:\n"
        f"1. Directly answer the user's question clearly and concisely in 2 to 3 short paragraphs.\n"
        f"2. Explain the concept and what caused the issue in their code.\n"
        f"3. Do NOT provide full code blocks unless the user explicitly requested code. If code is necessary, show only the 1 or 2 lines that change.\n"
        f"4. Focus on helping the user understand the concept so they can solve it themselves."
    )

    import asyncio
    try:
        result = await asyncio.wait_for(
            registry.complete(prompt=prompt, task_type="reason", max_tokens=450),
            timeout=30.0
        )
        content = result.content
        if content.count("```") % 2 != 0:
            content += "\n```"
        model_used = result.model_name
        latency_ms = result.latency_ms
    except Exception as exc:
        # Smart pedagogical fallback
        q_low = question.lower()
        err_low = (error or "").lower()
        if "loop" in q_low or "syntax" in q_low:
            content = (
                f"### Python Loop Syntax Guide:\n\n"
                f"In Python, `for` loops follow this structure:\n"
                f"```python\n"
                f"for <item> in <iterable>:\n"
                f"    # body\n"
                f"```\n"
                f"- To iterate over elements directly: `for item in collection:`\n"
                f"- To iterate over indices: `for i in range(len(collection)):`\n"
                f"- To iterate over both index and element: `for i, item in enumerate(collection):`\n\n"
                f"In Python, keywords like `in` never go before the variable name (e.g. avoid `for in item items`)."
            )
        elif "mutable" in err_low or "append" in err_low or "default" in q_low or "assertionerror" in err_low:
            content = (
                f"### Python Mutable Default Argument Pitfall:\n\n"
                f"In Python, default arguments like `task_list=[]` are evaluated **once at function definition time**, not every time the function is called!\n\n"
                f"As a result, all calls sharing the default argument append to the **same list instance in memory**.\n\n"
                f"**The Idiomatic Fix**:\n"
                f"```python\n"
                f"def append_task(task_name, task_list=None):\n"
                f"    if task_list is None:\n"
                f"        task_list = []\n"
                f"    task_list.append(task_name)\n"
                f"    return task_list\n"
                f"```"
            )
        elif "typeerror" in err_low or "str" in err_low or "int" in err_low:
            content = (
                f"Regarding your question '{question}':\n\n"
                f"In Python, variables have strict dynamic types. When you initialize an accumulator like `total = \"\"`, "
                f"it becomes a string. Attempting to add an integer (`total += num`) raises `TypeError` because `+` on strings means concatenation, "
                f"not numerical addition. To fix it, either initialize `total = 0` (for math) or use `total += str(num)` (for string building)."
            )
        elif "indexerror" in err_low or "range" in err_low:
            content = (
                f"Regarding your question '{question}':\n\n"
                f"Python lists use 0-based indexing from `0` to `len(list) - 1`. If your loop runs to `len(list)` or starts at `1` "
                f"without adjusting, it will attempt to access an index that doesn't exist."
            )
        else:
            content = (
                f"Regarding your question '{question}':\n\n"
                f"In {topic}, review how data types and flow pass through your functions. "
                f"Check that variables are initialized to the intended type before using them in operations."
            )
        model_used = "smart-rules"
        latency_ms = 0.0

    return {
        "question": question,
        "answer": content,
        "topic": topic,
        "model_used": model_used,
        "latency_ms": latency_ms,
    }


async def explain_runtime_error(
    topic: str,
    error: str,
    code: str = "",
    file_path: str = ""
) -> Dict[str, Any]:
    """Provide a line-by-line pedagogical breakdown of a runtime crash."""
    prompt = (
        f"You are a concise, sharp programming tutor.\n"
        f"Topic: {topic}\n"
        f"File: {file_path or 'unknown'}\n"
        f"Error: {error}\n"
        f"Code Context:\n```\n{code or 'No snippet provided'}\n```\n\n"
        f"Instructions:\n"
        f"- Be extremely concise (maximum 2 to 4 sentences).\n"
        f"- State directly what went wrong and which variable/line caused it.\n"
        f"- Explain the conceptual fix in plain words.\n"
        f"- DO NOT write code blocks or full rewritten functions unless strictly necessary or explicitly requested.\n"
        f"- Help the user understand the reason so they can solve it themselves."
    )

    import asyncio
    try:
        result = await asyncio.wait_for(
            registry.complete(prompt=prompt, task_type="reason", max_tokens=250),
            timeout=30.0
        )
        content = result.content
        if content.count("```") % 2 != 0:
            content += "\n```"
        model_used = result.model_name
        latency_ms = result.latency_ms
    except Exception:
        err_low = error.lower()
        if "zerodivisionerror" in err_low or "division by zero" in err_low:
            content = (
                "A `ZeroDivisionError` occurred because the denominator is 0. "
                "In this code, no elements matched your filter condition, making the list empty (`len = 0`). "
                "Check if the filtered list is empty before dividing, or return 0 if no matching items exist."
            )
        elif "assertionerror" in err_low or "assert" in err_low or "task" in err_low or "append" in err_low:
            content = (
                "In Python, default arguments like `task_list=[]` are evaluated only once when the function is defined, "
                "so every subsequent call reuses the exact same list in memory. "
                "To fix this, set the default to `None` and initialize a fresh `[]` inside the function body."
            )
        elif "typeerror" in err_low and ("concatenate" in err_low or "str" in err_low):
            content = (
                "Python cannot combine a string and an integer with `+`. "
                "Your accumulator was initialized as an empty string `\"\"` instead of a number. "
                "Initialize it to `0` for numeric addition, or convert values with `str()` for text concatenation."
            )
        elif "indexerror" in err_low:
            content = (
                "Lists in Python use 0-based indexing from `0` to `len - 1`. "
                "The loop or indexing operation tried to access an index that exceeds the list bounds. "
                "Adjust the range to `range(len(items))` so it stops before the boundary."
            )
        elif "keyerror" in err_low:
            content = (
                f"The dictionary does not contain the specified key. "
                f"Use `dict.get(key, default)` or check with `if key in dict:` before accessing it."
            )
        elif "recursionerror" in err_low or "recursion" in err_low:
            content = (
                "The maximum recursion depth was exceeded because the function calls itself without reaching a stopping condition. "
                "Add a base case to return before triggering another recursive call."
            )
        elif "referenceerror" in err_low or "initialization" in err_low:
            content = (
                "A variable was referenced before it was initialized in the Temporal Dead Zone. "
                "Ensure the variable is declared and assigned before any line attempts to read it."
            )
        elif "json" in err_low or "syntaxerror" in err_low or "token" in err_low:
            content = (
                "JSON parsing failed due to malformed syntax (such as trailing commas, unquoted keys, or single quotes). "
                "Validate that the input conforms strictly to valid JSON before calling `JSON.parse()`."
            )
        else:
            content = f"Runtime error `{error}` occurred. Check variable initialization, types, and logic boundaries in this function."
        model_used = "smart-rules"
        latency_ms = 0.0

    return {
        "error": error,
        "explanation": content,
        "topic": topic,
        "model_used": model_used,
        "latency_ms": latency_ms,
    }


async def chat_with_tutor(
    message: str,
    model_name: Optional[str] = None,
    image_base64: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Handle conversational multi-turn chat with the Tesseract AI Tutor."""
    if model_name:
        registry.set_active_model(model_name)

    # Build conversational prompt
    conversation_lines = []
    if history:
        for turn in history[-6:]:
            role = turn.get("role", "user").capitalize()
            txt = turn.get("content", "")
            if txt:
                conversation_lines.append(f"{role}: {txt}")

    conversation_context = "\n".join(conversation_lines)
    if conversation_context:
        prompt = (
            "You are Tesseract AI Tutor, an expert, concise, and helpful programming assistant.\n"
            "Recent conversation history:\n"
            f"{conversation_context}\n\n"
            f"User: {message}\n"
            "Assistant:"
        )
    else:
        prompt = (
            "You are Tesseract AI Tutor, an expert, concise, and helpful programming assistant.\n"
            f"User: {message}\n\n"
            "Instructions:\n"
            "- Answer clearly and concisely with direct explanations.\n"
            "- When providing code, format in clean markdown code blocks with the language tag.\n"
            "- If an image was attached, analyze the screenshot/diagram thoroughly.\n"
            "- Finish your thought completely and close all code blocks with ```."
        )

    images = [image_base64] if image_base64 else None

    import asyncio
    try:
        result = await asyncio.wait_for(
            registry.complete(
                prompt=prompt,
                task_type="reason",
                max_tokens=600,
                temperature=0.3,
                images=images
            ),
            timeout=45.0
        )
        content = result.content
        if content.count("```") % 2 != 0:
            content += "\n```"
        model_used = result.model_name
        latency_ms = result.latency_ms
    except Exception as exc:
        model_used = model_name or registry.active_model_name
        latency_ms = 0.0
        content = f"Tesseract Tutor response: {message}\n\n(AI inference timed out or model was busy. Please try again.)"

    return {
        "reply": content,
        "model_used": model_used,
        "latency_ms": latency_ms,
        "has_image": bool(image_base64)
    }


