"""
Intelligent Code Concept and Topic Extractor for Tesseract.
Analyzes AST (Abstract Syntax Tree) and code semantics to identify programming
domains, specific subtopics, and algorithmic paradigms present in the active code.
"""

from __future__ import annotations

import ast
import os
import re
from typing import Any, Dict, List, Optional


def extract_code_concepts(file_path: str, code: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze file path and code content to extract:
    - domain: e.g. "python", "c", "javascript", "algorithms"
    - primary_topic: the main concept represented
    - concepts: list of specific subtopics and programming patterns
    """
    if not code and file_path and os.path.exists(file_path) and os.path.isfile(file_path):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
        except Exception:
            code = ""

    code = code or ""
    lower_path = (file_path or "").lower()

    # Default fallback
    domain = "python" if lower_path.endswith(".py") else \
             "c" if lower_path.endswith((".c", ".h", ".cpp")) else \
             "javascript" if lower_path.endswith((".js", ".ts")) else "general"

    primary_topic = "General Programming"
    concepts: List[str] = []

    # 1. PYTHON AST & SEMANTIC ANALYSIS
    if domain == "python" or lower_path.endswith(".py"):
        domain = "python"
        parsed_ast = None
        try:
            parsed_ast = ast.parse(code)
        except Exception:
            pass

        # Check for specific algorithms / data structures
        has_classes = False
        has_recursion = False
        has_async = False
        has_dp = False
        has_tree = False
        has_linked_list = False
        has_math_division = False
        has_try_except = False

        if parsed_ast:
            for node in ast.walk(parsed_ast):
                if isinstance(node, ast.ClassDef):
                    has_classes = True
                    cname = node.name.lower()
                    if any(w in cname for w in ["tree", "bst", "node", "binary"]):
                        has_tree = True
                    if any(w in cname for w in ["lru", "cache", "list", "linked"]):
                        has_linked_list = True

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    fname = node.name
                    # Check if function calls itself (recursion)
                    for sub in ast.walk(node):
                        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id == fname:
                            has_recursion = True

                elif isinstance(node, (ast.AsyncFunctionDef, ast.Await)):
                    has_async = True

                elif isinstance(node, ast.Try):
                    has_try_except = True

                elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv)):
                    has_math_division = True

        # Regex & semantic heuristics
        lower_code = code.lower()
        has_arena = bool(re.search(r'\b(arena|bump|ctypes\.addressof|alignment)\b', lower_code))
        has_lru = bool(re.search(r'\b(lru|lrucache|doubly|mru)\b', lower_code))
        has_tree = bool(re.search(r'\b(bst|binarysearchtree|tree|inorder|preorder)\b', lower_code))
        has_dp = bool(re.search(r'\b(dp\[|memo|dynamic programming|knapsack|tabulation)\b', lower_code))
        has_async = bool(re.search(r'\b(asyncio|async def|await\s+|queue\.get|queue\.put)\b', lower_code))

        # Classify Primary Topic & Concepts
        if has_lru:
            primary_topic = "LRU Cache & Linked Lists"
            concepts.extend(["LRU Cache Design", "Doubly Linked Lists", "Hash Map Fast Lookups", "Classes & Object Design"])
        elif has_arena:
            primary_topic = "Memory Arena Allocator"
            concepts.extend(["Memory Arena Allocator", "Pointer Alignment & Offsets", "Low-Level Memory Management"])
        elif has_tree:
            primary_topic = "Binary Search Trees"
            concepts.extend(["Binary Search Trees", "Recursion & Traversals", "Classes & Object Design"])
        elif has_dp:
            primary_topic = "Dynamic Programming"
            concepts.extend(["Dynamic Programming", "Memoization & 2D Tables", "Optimization Algorithms"])
        elif has_async:
            primary_topic = "Async & Concurrency"
            concepts.extend(["Async / Await Concurrency", "Producer-Consumer Queues", "Task Orchestration"])
        elif has_recursion:
            primary_topic = "Recursion & Call Stack"
            concepts.extend(["Recursion & Call Stack", "Divide and Conquer", "Function Call Frames"])
        elif has_math_division:
            primary_topic = "Zero Division & Math Safety"
            concepts.extend(["Zero Division & Math Safety", "Guard Conditions", "Data Aggregation"])
        else:
            primary_topic = "Python Core"
            concepts.extend(["Python Syntax & Variables", "Control Flow & Loops", "Function Scoping"])

        if has_try_except and "Exception Handling" not in concepts:
            concepts.append("Exception & Error Handling")

    # 2. C & SYSTEMS ANALYSIS
    elif domain == "c" or lower_path.endswith((".c", ".h", ".cpp")):
        domain = "c"
        lower_code = code.lower()
        has_arena = "arena" in lower_code or "bump" in lower_code or "region" in lower_code
        has_malloc = "malloc" in lower_code or "calloc" in lower_code or "free(" in lower_code
        has_pointers = "*" in code or "->" in code or "&" in code
        has_null = "null" in lower_code
        has_struct = "struct" in lower_code

        if has_arena:
            primary_topic = "Memory Arena Allocator"
            concepts.extend(["Memory Arena Allocator", "Pointers & Byte Offsets", "Memory Alignment & NULL Safety"])
        elif has_malloc:
            primary_topic = "Dynamic Memory & Malloc"
            concepts.extend(["Dynamic Memory (malloc/free)", "Heap Allocation Life-Cycles", "Pointers & Dereferencing"])
        elif has_pointers:
            primary_topic = "Pointers & Dereferencing"
            concepts.extend(["Pointers & Dereferencing", "Address Operators", "NULL Pointer Safety"])
        else:
            primary_topic = "C Control Flow"
            concepts.extend(["Variables & Types", "Arrays & Buffers", "Functions & Scope"])

        if has_null and "NULL Pointer Safety" not in concepts:
            concepts.append("NULL Pointer Safety")
        if has_struct and "Structs & Memory Layout" not in concepts:
            concepts.append("Structs & Memory Layout")

    # 3. JAVASCRIPT ANALYSIS
    elif domain == "javascript" or lower_path.endswith((".js", ".ts", ".html")):
        domain = "javascript"
        lower_code = code.lower()
        has_emitter = "eventemitter" in lower_code or "listener" in lower_code or "emit(" in lower_code or "subscribe" in lower_code
        has_async = "async " in lower_code or "await " in lower_code or "promise" in lower_code
        has_json = "json.parse" in lower_code or "json.stringify" in lower_code
        has_dom = "addeventlistener" in lower_code or "document.getelement" in lower_code or "queryselector" in lower_code

        if has_emitter:
            primary_topic = "Event-Driven PubSub"
            concepts.extend(["Event-Driven Architecture", "Closures & Callback Registries", "Observer Pattern"])
        elif has_async:
            primary_topic = "Async / Await & Promises"
            concepts.extend(["Async / Await & Promises", "Microtask Queues", "Error Boundaries"])
        elif has_json:
            primary_topic = "JSON Serialization"
            concepts.extend(["JSON Parsing & Serialization", "Schema Validation", "Safe Type Parsing"])
        elif has_dom:
            primary_topic = "DOM Event Binding"
            concepts.extend(["DOM Event Binding", "Event Propagation", "Null Element Guards"])
        else:
            primary_topic = "JavaScript Scope"
            concepts.extend(["Variable Scope & TDZ", "Functions & Closures", "Object Prototypes"])

    # Ensure uniqueness while preserving order
    seen = set()
    unique_concepts = []
    for c in concepts:
        if c not in seen:
            seen.add(c)
            unique_concepts.append(c)

    return {
        "domain": domain,
        "primary_topic": primary_topic,
        "concepts": unique_concepts or [primary_topic],
        "file_path": file_path,
    }
