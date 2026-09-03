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
        f"1. Directly answer the user's question clearly and concisely.\n"
        f"2. Reference their exact code lines and error to explain why it happens.\n"
        f"3. Offer a pedagogical tip or hint on how to fix it cleanly.\n"
        f"Keep the answer under 3 short paragraphs."
    )

    import asyncio
    try:
        result = await asyncio.wait_for(
            registry.complete(prompt=prompt, task_type="reason", max_tokens=220),
            timeout=30.0
        )
        content = result.content
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
        f"You are an expert programming tutor. Explain this runtime crash clearly.\n"
        f"Topic: {topic}\n"
        f"File: {file_path or 'unknown'}\n"
        f"Error: {error}\n"
        f"Code Context:\n```\n{code or 'No snippet provided'}\n```\n\n"
        f"Explain in plain English:\n"
        f"1. What this error means.\n"
        f"2. Exactly which line and variables caused the crash in the code above.\n"
        f"3. How to fix it properly."
    )

    import asyncio
    try:
        result = await asyncio.wait_for(
            registry.complete(prompt=prompt, task_type="reason", max_tokens=220),
            timeout=30.0
        )
        content = result.content
        model_used = result.model_name
        latency_ms = result.latency_ms
    except Exception:
        err_low = error.lower()
        if "assertionerror" in err_low or "assert" in err_low or "task" in err_low or "append" in err_low:
            content = (
                "### Why this `AssertionError` occurred (Mutable Default Argument Bug):\n\n"
                "1. **What it means**: An assertion test failed because `len(user2_tasks)` was 2 instead of 1.\n"
                "2. **Why it crashed**: In Python, default argument values like `task_list=[]` are evaluated **only once when the function is defined**, not on each call! All calls sharing the default argument append to the **exact same list instance in memory**, causing unexpected data leakage across calls.\n"
                "3. **How to fix**:\n"
                "```python\n"
                "def append_task(task_name, task_list=None):\n"
                "    if task_list is None:\n"
                "        task_list = []\n"
                "    task_list.append(task_name)\n"
                "    return task_list\n"
                "```"
            )
        elif "typeerror" in err_low and ("concatenate" in err_low or "str" in err_low):
            content = (
                "### Why this `TypeError` occurred:\n\n"
                "1. **What it means**: Python cannot automatically combine a string and an integer using `+`.\n"
                "2. **Why it crashed**: The accumulator was initialized as an empty string (`total = \"\"`), but the loop passed integer numbers (`1, 2, 3...`). Python doesn't know whether you wanted to convert the int to text or do math!\n"
                "3. **How to fix**:\n"
                "- If you want to sum numbers: change `total = \"\"` to `total = 0`.\n"
                "- If you want to build a string: use `total += str(num)`."
            )
        elif "indexerror" in err_low:
            content = (
                "### Why this `IndexError` occurred:\n\n"
                "1. **What it means**: Python attempted to fetch an item at an index outside the valid bounds of the list.\n"
                "2. **Why it crashed**: Python lists are 0-indexed (indices `0` to `N-1`). Accessing index `N` or beyond throws `IndexError`.\n"
                "3. **How to fix**: Ensure your range runs `range(len(items))` rather than `range(1, len(items) + 1)`."
            )
        elif "keyerror" in err_low:
            content = (
                "### Why this `KeyError` occurred:\n\n"
                "1. **What it means**: The dictionary does not contain the specified key.\n"
                "2. **How to fix**: Use `dict.get(key, default)` or verify with `if key in dict:` before indexing."
            )
        elif "recursionerror" in err_low or "recursion" in err_low:
            content = (
                "### Why this `RecursionError` occurred:\n\n"
                "1. **What it means**: The maximum recursion depth was exceeded.\n"
                "2. **Why it crashed**: The recursive function called itself infinitely without reaching a base case.\n"
                "3. **How to fix**: Add a base case (e.g. `if n <= 0: return 0`) to terminate recursion."
            )
        elif "referenceerror" in err_low or "initialization" in err_low:
            content = (
                "### Why this `ReferenceError` occurred:\n\n"
                "1. **What it means**: A variable was accessed before its declaration (Temporal Dead Zone).\n"
                "2. **How to fix**: Declare and initialize the variable before reading from it."
            )
        else:
            content = f"### Error Breakdown ({topic}):\n\nError: `{error}`\nCheck variable types and function arguments in your active file."
        model_used = "smart-rules"
        latency_ms = 0.0

    return {
        "error": error,
        "explanation": content,
        "topic": topic,
        "model_used": model_used,
        "latency_ms": latency_ms,
    }

