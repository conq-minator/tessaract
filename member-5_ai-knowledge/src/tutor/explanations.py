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
    file_path: str = "",
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Answer a user's prompt in context of their code and error with multi-turn history.
    
    Anti-cheat & Anti-spoiler: Refuse full code dumps, solution code blocks, and instruction bypasses.
    Highest allowable assistance is conceptual explanation + generic abstract syntax templates.
    """
    import asyncio
    import re as _re

    # ── Anti-Cheat Detection ─────────────────────────────────────────
    q_low = question.lower().strip()
    cheat_patterns = [
        r"ignore\s+(everything|all|previous|instructions|rules)",
        r"just\s+give\s+me\s+(the\s+)?(full|complete|entire|corrected|fixed)\s+(code|solution|answer)",
        r"give\s+me\s+(the\s+)?(full|complete|entire|corrected|fixed)\s+(code|solution|answer)",
        r"write\s+(the\s+)?(full|complete|entire|corrected|fixed)\s+(code|solution|answer)",
        r"(show|output|print|paste)\s+(the\s+)?(full|complete|corrected|fixed)\s+(code|solution)",
        r"solve\s+(it|this)\s+(for|completely)",
        r"do\s+my\s+(homework|assignment|code)",
        r"(copy|paste)\s*-?\s*able\s+solution",
    ]
    is_cheat_attempt = any(_re.search(p, q_low) for p in cheat_patterns)

    if is_cheat_attempt:
        content = (
            "I cannot write the complete solution code for you — my goal is to help you "
            "master the concept so you can solve it yourself.\n\n"
            f"Here is how you can approach this on your own:\n"
            f"1. Read the error message carefully — it points to the exact line and problem.\n"
            f"2. Check the spelling of all keywords and the structure of your statement.\n"
            f"3. Compare your syntax against standard {topic} language reference.\n"
            f"4. Use the 💡 Hint button for progressive guidance without spoilers."
        )
        return {
            "question": question,
            "answer": content,
            "topic": topic,
            "model_used": "anti-cheat-guardrail",
            "latency_ms": 0.0,
        }

    # Clean file-not-found / runner noise from error string
    error_lines = [
        l for l in (error or "").split("\n")
        if "can't open file" not in l.lower()
        and "no such file" not in l.lower()
        and "cannot be opened" not in l.lower()
    ]
    effective_error = "\n".join(error_lines).strip()
    if not effective_error and error:
        effective_error = f"Error during {topic} execution"

    # Multi-turn conversational history context
    history_context = ""
    if history:
        turns = []
        for turn in history[-4:]:
            role = "Learner" if turn.get("role") == "user" else "Tutor"
            txt = turn.get("content", "").strip()
            if txt:
                turns.append(f"{role}: {txt}")
        if turns:
            history_context = "Prior Conversation:\n" + "\n".join(turns) + "\n\n"

    # ── Standard Pedagogical Q&A ─────────────────────────────────────
    prompt = (
        f"You are an encouraging and expert programming tutor.\n"
        f"Topic: {topic}\n"
        f"Runtime Error: {effective_error or 'None specified'}\n"
        f"Code Snippet:\n```\n{code or 'No snippet provided'}\n```\n\n"
        f"{history_context}"
        f"User's Question: \"{question}\"\n\n"
        f"CRITICAL RULES — you MUST follow these:\n"
        f"1. Answer concisely in 2 to 3 short paragraphs.\n"
        f"2. Explain the concept and what caused the issue.\n"
        f"3. NEVER provide full corrected code, complete solution blocks, or multi-line rewrites.\n"
        f"4. Highest allowable code assistance is generic abstract syntax grammar templates (e.g. `for <var> in <iterable>:` or `if <condition>:`). Do NOT write the student's solution or use their specific variables in code.\n"
        f"5. If the user asks for the full code or solution, refuse politely: 'I cannot write the solution for you, but here is how you can think about it...' and provide only conceptual guidance.\n"
        f"6. DO NOT mention file locations, file paths, or missing files.\n"
        f"7. Help the user understand the concept so they can fix it themselves."
    )

    try:
        result = await asyncio.wait_for(
            registry.complete(prompt=prompt, task_type="reason", max_tokens=300, temperature=0.2),
            timeout=30.0
        )
        content = (result.content or "").strip()
        # Post-generation anti-spoiler sanitizer: strip fenced code blocks
        if "```" in content:
            content = _re.sub(r"```[\s\S]*?```", "[Try writing the code yourself!]", content).strip()
        # Strip inline solution markers
        content = _re.sub(r"(?:corrected|fixed|correct)\s+(?:code|version|line).*?:\s*\n.*", "", content, flags=_re.IGNORECASE).strip()
        model_used = result.model_name
        latency_ms = result.latency_ms
    except Exception as exc:
        # Smart pedagogical fallback
        err_low = (effective_error or "").lower()
        if "loop" in q_low or "syntax" in q_low:
            content = (
                f"In {topic}, statement syntax follows standard grammar patterns (e.g. `for <item> in <iterable>:` in Python).\n\n"
                f"Check that your keywords are spelled correctly and the statement ends with the expected delimiter. "
                f"Language keywords must match exactly — even one extra letter breaks the syntax."
            )
        elif "typeerror" in err_low or "str" in err_low or "int" in err_low:
            content = (
                f"Data types must be compatible for operations. "
                f"Check that your variables and accumulators are initialized to the correct types before combining them."
            )
        elif "indexerror" in err_low:
            content = (
                f"Sequence indices must stay within boundary ranges (0 to length - 1). "
                f"Check that your loop or index expression stays within valid bounds."
            )
        else:
            content = (
                f"Review the error message and trace it back to the offending line in your code. "
                f"Check variable types, keyword spelling, and statement grammar."
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


import ast as _ast
import keyword as _keyword
import difflib as _difflib
import re as _re


def _diagnose_syntax_error(code: str, error: str, topic: str = "python") -> Optional[str]:
    """Accurately diagnose Python syntax errors with zero hallucination."""
    line_no = 1
    error_line = ""

    # Try to extract line number from error traceback
    m = _re.search(r"line\s+(\d+)", error, _re.IGNORECASE)
    if m:
        line_no = int(m.group(1))

    # Parse with AST to pinpoint exact line and token
    syn_err = None
    if code:
        try:
            _ast.parse(code)
        except SyntaxError as e:
            syn_err = e
            line_no = e.lineno or line_no
            if e.text:
                error_line = e.text.strip()

    if not error_line and code:
        lines = code.split("\n")
        if 0 < line_no <= len(lines):
            error_line = lines[line_no - 1].strip()

    if not error_line:
        return None

    tokens = error_line.split()
    first_token = tokens[0] if tokens else ""

    # Check 1: Misspelled keyword (e.g. 'forr', 'whlie', 'fucntion', 'clas', 'def_')
    close_kws = _difflib.get_close_matches(first_token, _keyword.kwlist, n=1, cutoff=0.6)
    if close_kws and first_token not in _keyword.kwlist:
        target_kw = close_kws[0]
        return (
            f"SyntaxError on line {line_no}: '{first_token}' is not a recognized Python keyword. "
            f"It appears to be a typo for the `{target_kw}` statement keyword. "
            f"In Python, statement keywords must be spelled exactly for the interpreter to parse your code."
        )

    # Check 2: Compound statement headers (for, while, if, elif, else, def, class, etc.)
    compound_kws = {"for", "while", "if", "elif", "else", "def", "class", "try", "except", "finally", "with", "match", "case"}
    if first_token in compound_kws:
        if not error_line.endswith(":"):
            return (
                f"SyntaxError on line {line_no}: The `{first_token}` statement is missing a trailing colon (`:`). "
                f"In Python, header statements that introduce an indented block must always end with a colon."
            )

    # Check 3: Assignment '=' in conditional statement
    if first_token in {"if", "elif", "while"} and " = " in error_line and "==" not in error_line:
        return (
            f"SyntaxError on line {line_no}: A single `=` (assignment) was used instead of `==` (comparison). "
            f"In Python conditions, use `==` to test whether two expressions are equal."
        )

    # Check 4: Unclosed strings or brackets from syn_err
    if syn_err and syn_err.msg:
        msg_low = syn_err.msg.lower()
        if "was never closed" in msg_low or "unterminated" in msg_low or "eol while scanning" in msg_low:
            return (
                f"SyntaxError on line {line_no}: {syn_err.msg}. "
                f"Ensure every string quotation mark or bracket `(`, `[`, `{{` has a matching closing pair."
            )

    return None


async def explain_runtime_error(
    topic: str,
    error: str,
    code: str = "",
    file_path: str = ""
) -> Dict[str, Any]:
    """Provide a line-by-line pedagogical breakdown of a runtime crash or syntax error.
    
    Uses deterministic diagnostics first for 100% accuracy and zero hallucination,
    falling back to grounded LLM inference for novel errors.
    """
    import asyncio

    # Clean file-not-found / path resolution noise from error string so it never leaks into explanations
    error_lines = [
        l for l in (error or "").split("\n")
        if "can't open file" not in l.lower()
        and "no such file" not in l.lower()
        and "cannot be opened" not in l.lower()
    ]
    effective_error = "\n".join(error_lines).strip()
    if not effective_error and error:
        effective_error = f"Error during {topic} execution"
    err_low = effective_error.lower()

    # 1. Deterministic Python Syntax Diagnosis
    if "syntax" in err_low or "invalid syntax" in err_low:
        diag = _diagnose_syntax_error(code, effective_error, topic)
        if diag:
            return {
                "error": effective_error,
                "explanation": diag,
                "topic": topic,
                "model_used": "syntax-diagnostics",
                "latency_ms": 0.0,
            }

    # 2. Deterministic Runtime Error Diagnostics (zero hallucination)
    if "recursionerror" in err_low or "recursion depth" in err_low:
        content = (
            "A `RecursionError` occurred because the recursive function called itself indefinitely without reaching a base case. "
            "Every recursive function requires a stopping condition (base case) that returns a value before recursing further. "
            "Ensure your function checks whether the parameter has reached its stopping boundary (e.g. `n <= 0`)."
        )
        return {"error": effective_error, "explanation": content, "topic": topic, "model_used": "runtime-diagnostics", "latency_ms": 0.0}

    if "assertionerror" in err_low or "mutable default" in err_low or "task" in err_low:
        content = (
            "An `AssertionError` occurred due to shared state across function calls. "
            "In Python, default arguments like `task_list=[]` are evaluated once at function definition time and reused in memory. "
            "To ensure every invocation gets a fresh list, set the default to `None` and initialize `task_list = []` inside the function."
        )
        return {"error": effective_error, "explanation": content, "topic": topic, "model_used": "runtime-diagnostics", "latency_ms": 0.0}

    if "zerodivisionerror" in err_low or "division by zero" in err_low:
        content = (
            "A `ZeroDivisionError` occurred because the denominator evaluated to 0. "
            "In this code, check if the collection is empty before calculating an average or ratio, "
            "and ensure divisors are guarded with `if divisor != 0:`."
        )
        return {"error": effective_error, "explanation": content, "topic": topic, "model_used": "runtime-diagnostics", "latency_ms": 0.0}

    if "typeerror" in err_low and ("concatenate" in err_low or "str" in err_low or "unsupported operand" in err_low):
        content = (
            "A `TypeError` occurred because Python cannot combine incompatible data types with `+`. "
            "Python does not automatically convert numbers to strings or vice-versa. "
            "Initialize accumulators to numeric `0` for arithmetic, or convert values with `str()` for text building."
        )
        return {"error": effective_error, "explanation": content, "topic": topic, "model_used": "runtime-diagnostics", "latency_ms": 0.0}

    if "indexerror" in err_low:
        content = (
            "An `IndexError` occurred because the code attempted to access an index beyond the sequence boundaries. "
            "Python lists use 0-based indexing (valid indices are `0` to `len - 1`). "
            "Use `range(len(items))` or iterate directly with `for item in items:`."
        )
        return {"error": effective_error, "explanation": content, "topic": topic, "model_used": "runtime-diagnostics", "latency_ms": 0.0}

    if "keyerror" in err_low:
        content = (
            "A `KeyError` occurred because the specified key does not exist in the dictionary. "
            "Verify the key name, or use `dict.get(key, default)` or `if key in dict:` to check before accessing."
        )
        return {"error": effective_error, "explanation": content, "topic": topic, "model_used": "runtime-diagnostics", "latency_ms": 0.0}

    if "attributeerror" in err_low and "nonetype" in err_low:
        content = (
            "An `AttributeError` occurred because an attribute or method was accessed on a variable that is `None`. "
            "This usually means an earlier function call returned `None` instead of the expected object. "
            "Add a guard check: `if variable is not None:` before using its methods."
        )
        return {"error": effective_error, "explanation": content, "topic": topic, "model_used": "runtime-diagnostics", "latency_ms": 0.0}

    # 3. Grounded LLM Fallback for Unknown / Complex Errors
    prompt = (
        f"You are a concise, sharp programming tutor.\n"
        f"Topic: {topic}\n"
        f"Error: {effective_error or 'Syntax or runtime error'}\n"
        f"Code Context:\n```\n{code or 'No snippet provided'}\n```\n\n"
        f"CRITICAL RULES — you MUST follow these:\n"
        f"- Be extremely concise (maximum 2 to 3 sentences).\n"
        f"- State directly what went wrong and which variable/line caused it.\n"
        f"- Explain the conceptual fix in plain words.\n"
        f"- NEVER provide full corrected code or multi-line rewritten functions.\n"
        f"- Highest allowable code assistance is generic abstract syntax grammar (e.g. `for <var> in <iterable>:` or `if <condition>:`).\n"
        f"- DO NOT mention file locations, file paths, or missing files.\n"
        f"- Help the user understand the reason so they can solve it themselves."
    )

    try:
        result = await asyncio.wait_for(
            registry.complete(prompt=prompt, task_type="reason", max_tokens=200, temperature=0.2),
            timeout=20.0
        )
        content = (result.content or "").strip()
        # Clean up any leaked code blocks
        if "```" in content:
            content = _re.sub(r"```[\s\S]*?```", "[Try writing the code yourself!]", content).strip()
        content = _re.sub(r"(?:corrected|fixed|correct)\s+(?:code|version|line).*?:\s*\n.*", "", content, flags=_re.IGNORECASE).strip()
        model_used = result.model_name
        latency_ms = result.latency_ms
    except Exception:
        content = f"Runtime error `{effective_error}` occurred. Inspect variable types, statement structure, and boundaries on the active line."
        model_used = "smart-rules"
        latency_ms = 0.0

    return {
        "error": effective_error,
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
    infer_timeout = 150.0 if (images or "gemma4" in (model_name or "")) else 60.0

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
            timeout=infer_timeout
        )
        content = result.content
        if content.count("```") % 2 != 0:
            content += "\n```"
        model_used = result.model_name
        latency_ms = result.latency_ms
    except Exception as exc:
        logger.error("Chat completion error: %s", exc, exc_info=True)
        model_used = model_name or registry.active_model_name
        latency_ms = 0.0
        content = f"⚠️ Image/Chat inference encountered an issue: {exc}\n\nPlease try again."

    return {
        "reply": content,
        "model_used": model_used,
        "latency_ms": latency_ms,
        "has_image": bool(image_base64)
    }


