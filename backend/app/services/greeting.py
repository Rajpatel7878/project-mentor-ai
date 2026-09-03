"""Proactive greeting and ambient intelligence."""

from datetime import datetime


def get_time_of_day() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"


def generate_greeting(user_name: str = "Sir", project_phase: str = "building") -> dict:
    time_of_day = get_time_of_day()
    greeting = f"Good {time_of_day}, {user_name}. How can I help you today, sir?"

    suggestions_map = {
        "ideation": [
            "Shall we refine your product vision and target audience?",
            "Would you like to explore competitive landscape analysis?",
        ],
        "building": [
            "Shall we review today's development priorities?",
            "Would you like a sprint planning session?",
        ],
        "testing": [
            "Should we run through the test coverage report?",
            "Would you like to prioritize bug fixes for launch?",
        ],
        "launching": [
            "Shall we finalize the go-to-market checklist?",
            "Would you like to review launch day communications?",
        ],
    }

    return {
        "greeting": greeting,
        "time_of_day": time_of_day,
        "user_name": user_name,
        "proactive_suggestions": suggestions_map.get(project_phase, suggestions_map["building"]),
    }
