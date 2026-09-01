from typing import Dict, Any, List

def get_mock_knowledge_graph() -> Dict[str, Any]:
    return {
        "nodes": [
            {"id": "Variables", "group": 1, "confidence": 0.95, "status": "mastered"},
            {"id": "Pointers", "group": 1, "confidence": 0.40, "status": "developing"},
            {"id": "Memory Allocation", "group": 2, "confidence": 0.20, "status": "struggling"},
            {"id": "Dereferencing", "group": 1, "confidence": 0.30, "status": "struggling"},
            {"id": "NULL handling", "group": 1, "confidence": 0.80, "status": "good"}
        ],
        "links": [
            {"source": "Variables", "target": "Pointers", "value": 1},
            {"source": "Pointers", "target": "Memory Allocation", "value": 2},
            {"source": "Pointers", "target": "Dereferencing", "value": 2},
            {"source": "Pointers", "target": "NULL handling", "value": 2}
        ]
    }

def get_mock_recommendations() -> List[Dict[str, Any]]:
    return [
        {
            "id": "rec-1",
            "title": "Understanding Pointers in C",
            "url": "https://example.com/pointers",
            "type": "documentation",
            "format": "Article",
            "difficulty": "Beginner"
        },
        {
            "id": "rec-2",
            "title": "Interactive Memory Management",
            "url": "https://example.com/interactive-memory",
            "type": "exercise",
            "format": "Interactive",
            "difficulty": "Intermediate"
        }
    ]
