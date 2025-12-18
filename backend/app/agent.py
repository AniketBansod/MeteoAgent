import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env explicitly from backend BEFORE importing tools
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool

from app.tools import get_weather_json, compare_weather, summarize_forecast
from app.prompts import SYSTEM_PROMPT
from app.schemas import ReasoningStep


def get_agent():
    reasoning_steps: list[ReasoningStep] = []

    def weather_tool(city: str) -> str:
        reasoning_steps.append(ReasoningStep(step="tool_call", detail=f"Fetching weather for {city}"))
        data = get_weather_json(city)
        if not data:
            reasoning_steps.append(ReasoningStep(step="error", detail=f"Weather unavailable for {city}"))
            return f"Weather unavailable for {city}"
        reasoning_steps.append(ReasoningStep(step="tool_result", detail=f"Weather received for {city}"))
        # Return compact human string but the agent can still parse numbers in other flows
        return f"{data['city']}: {data['temp']}°C, humidity {data['humidity']}%, wind {data['wind_kmh']} km/h, {data['condition']}"

    def compare_tool(arg: str) -> str:
        # Input format: "city1, city2"
        parts = [p.strip() for p in (arg or "").split(",") if p.strip()]
        if len(parts) < 2:
            return "Provide two cities separated by a comma (e.g., Pune, Nashik)."
        c1, c2 = parts[0], parts[1]
        reasoning_steps.append(ReasoningStep(step="tool_call", detail=f"Comparing weather: {c1} vs {c2}"))
        res = compare_weather(c1, c2)
        if not res or not res.get("city1_weather") or not res.get("city2_weather"):
            reasoning_steps.append(ReasoningStep(step="error", detail="Comparison failed"))
            return "Unable to compare due to missing weather data."
        w1 = res["city1_weather"]; w2 = res["city2_weather"]
        win = res["winner"]
        reasoning_steps.append(ReasoningStep(step="tool_result", detail=f"Winner: {win}"))
        return (
            f"Winner: {win}\n"
            f"{w1['city']}: {w1['temp']}°C, {w1['humidity']}% hum, {w1['wind_kmh']} km/h wind\n"
            f"{w2['city']}: {w2['temp']}°C, {w2['humidity']}% hum, {w2['wind_kmh']} km/h wind"
        )

    tools = [
        Tool(
            name="WeatherTool",
            func=weather_tool,
            description="Get structured weather summary for a city"
        ),
        Tool(
            name="CompareWeather",
            func=compare_tool,
            description="Compare weather between two cities. Input format: 'city1, city2'"
        ),
        Tool(
            name="ForecastTool",
            func=lambda city: summarize_forecast(city),
            description="Provides next 5-day average forecast summary for a city. Input: city name"
        ),
    ]

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        reasoning_steps.append(ReasoningStep(step="error", detail="Missing OPENROUTER_API_KEY"))
        raise ValueError("OPENROUTER_API_KEY not configured")

    model_id = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    reasoning_steps.append(ReasoningStep(step="llm_init", detail=f"Initializing language model {model_id}"))

    llm = ChatOpenAI(
        model=model_id,
        temperature=0,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
    )

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=False,
        # Some versions accept agent_kwargs for system prompts; keep safe default.
        # agent_kwargs={"system_message": SYSTEM_PROMPT}
    )

    return agent, reasoning_steps
