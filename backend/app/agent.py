import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env explicitly from backend BEFORE importing tools
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

from app.intent import detect_intent
from app.tools import get_weather


def get_agent():
    reasoning_steps = []

    def executor(user_message: str) -> str:
        intent_result = detect_intent(user_message)

        reasoning_steps.append(
            f"Detected intent: {intent_result.intent}, "
            f"cities: {intent_result.cities}, "
            f"confidence: {intent_result.confidence}"
        )

        if not intent_result.cities:
            return "Please mention at least one city."

        # Phase 3.1 → single city only (multi-city in Phase 3.2)
        city = intent_result.cities[0]

        try:
            weather = get_weather(city)
            reasoning_steps.append(f"Weather fetched successfully for {city}")
            return weather
        except Exception as e:
            reasoning_steps.append(f"Weather fetch failed for {city}: {str(e)}")
            return f"Unable to fetch weather for {city}."

    return executor, reasoning_steps
