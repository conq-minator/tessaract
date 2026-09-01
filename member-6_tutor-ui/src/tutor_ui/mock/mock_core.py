from typing import Dict, Any, List

def get_mock_context() -> Dict[str, Any]:
    return {
        "subject": "C Programming",
        "topic": "Pointers",
        "application": "VS Code"
    }

def get_mock_friction() -> Dict[str, Any]:
    return {
        "score": 0.73,
        "level": "HIGH"
    }

def get_mock_episodes() -> List[Dict[str, Any]]:
    return [
        {
            "id": "ep-1",
            "topic": "Pointer Dereferencing",
            "duration_min": 20,
            "friction": 0.8,
            "status": "struggling"
        },
        {
            "id": "ep-2",
            "topic": "Variables",
            "duration_min": 5,
            "friction": 0.1,
            "status": "mastered"
        }
    ]

def get_mock_session() -> Dict[str, Any]:
    return {
        "id": "sesh-current",
        "duration": "2h 14m",
        "event_count": 47
    }

def get_mock_analytics() -> Dict[str, Any]:
    return {
        "total_time_tracked": "45h",
        "most_active_app": "VS Code",
        "recent_focus": "C Programming"
    }
