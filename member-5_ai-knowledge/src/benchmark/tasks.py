"""The 10 canonical benchmark tasks for evaluating Tesseract candidate models."""

from typing import List, Dict, Any

BENCHMARK_TASKS: List[Dict[str, Any]] = [
    {
        "id": "task-01-c-pointer-errors",
        "name": "Repeated C Pointer Errors Interpretation",
        "category": "reasoning",
        "prompt": (
            "A student had 4 segmentation faults in main.c at line 28 while attempting: int *p; *p = 10; "
            "Explain in 2 sentences why this crashed and how to fix it without copy-pasting code."
        ),
        "expected_keywords": ["uninitialized", "address", "allocate", "memory", "point"],
    },
    {
        "id": "task-02-python-learning-detection",
        "name": "Python Beginner Learning Detection",
        "category": "classification",
        "prompt": "Classify intent: The user is writing 'for i in range(10):', made a syntax error with indentation, then searched 'python for loop syntax'.",
        "labels": ["learning_syntax", "debugging_logic", "production_coding", "exploring"],
        "expected_label": "learning_syntax",
    },
    {
        "id": "task-03-youtube-learning-sequence",
        "name": "YouTube Learning Sequence Correlation",
        "category": "reasoning",
        "prompt": (
            "Event sequence: VS Code C error 'dereferencing pointer to incomplete type' -> "
            "Google search 'struct in c header file' -> YouTube watch 'C Structs and Header Files Tutorial (12 mins)'. "
            "Summarize the single concept the learner is attempting to understand in 5 words or less."
        ),
        "expected_keywords": ["struct", "header", "incomplete", "declaration"],
    },
    {
        "id": "task-04-vscode-debugging-struggle",
        "name": "VS Code Debugging Struggle Detection",
        "category": "classification",
        "prompt": "User ran the debugger 8 times on the same 10 lines of code in 15 minutes, toggling breakpoints on lines 12 and 14 without editing code.",
        "labels": ["high_friction", "normal_development", "code_review"],
        "expected_label": "high_friction",
    },
    {
        "id": "task-05-math-question",
        "name": "Mathematical Question Interpretation",
        "category": "reasoning",
        "prompt": "Evaluate: What is the derivative of f(x) = x^3 * e^(2x)? Show the product rule step.",
        "expected_keywords": ["3x^2", "2e^(2x)", "product rule", "e^(2x)"],
    },
    {
        "id": "task-06-diagram-interpretation",
        "name": "Technical Diagram Interpretation",
        "category": "reasoning",
        "prompt": "Diagram description: Node A points to Node B with edge 'prerequisite_of'. Node B points to Node C. What is the prerequisite order?",
        "expected_keywords": ["a", "b", "c", "order", "first"],
    },
    {
        "id": "task-07-intent-classification",
        "name": "User Intent Classification",
        "category": "classification",
        "prompt": "The user opened Firefox, visited docs.python.org/3/library/asyncio.html, and copied an example into test.py.",
        "labels": ["learning", "debugging", "idle", "administrative"],
        "expected_label": "learning",
    },
    {
        "id": "task-08-knowledge-gap-detection",
        "name": "Knowledge Gap Detection",
        "category": "reasoning",
        "prompt": (
            "User fails to implement binary search in C. They understand array indexing and loops, but struggle with mid = (low + high) / 2 and off-by-one loop termination. "
            "Identify the missing algorithmic prerequisite."
        ),
        "expected_keywords": ["boundary", "condition", "loop invariant", "off-by-one", "divide"],
    },
    {
        "id": "task-09-hint-generation",
        "name": "Level 1 Non-Spoiling Hint Generation",
        "category": "reasoning",
        "prompt": "User forgot 'return 0;' or 'return val;' inside a non-void C function. Give a Level 1 Hint without stating the return statement directly.",
        "expected_keywords": ["function", "promise", "value", "type", "expect"],
    },
    {
        "id": "task-10-practice-question-generation",
        "name": "Targeted Practice Question Generation",
        "category": "reasoning",
        "prompt": "Generate a 1-line puzzle testing whether the student knows if NULL in C evaluates to true or false in an if condition.",
        "expected_keywords": ["null", "if", "true", "false", "condition"],
    },
]
