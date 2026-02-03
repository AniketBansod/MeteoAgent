import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env explicitly from backend BEFORE importing tools
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool

from app.tools import (
    get_weather_json, 
    compare_weather, 
    summarize_forecast,
    memory_search,
    memory_save,
    format_memories_context,
)
from app.prompts import SYSTEM_PROMPT
from app.schemas import ReasoningStep


def get_llm():
    """Get configured ChatOpenAI instance for the agent."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not configured")

    model_id = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    
    return ChatOpenAI(
        model=model_id,
        temperature=0,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
    )


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


def chat_with_memory(
    user_message: str,
    user_id: int,
    reasoning_steps: list[ReasoningStep] | None = None,
) -> tuple[str, list[str], float]:
    """
    Chat flow with memory integration:
    
    1. memory_search(query) -> retrieve relevant past context
    2. Build prompt with memories + user message
    3. LLM generates response
    4. Return (answer, used_memories, latency_ms)
    
    NOTE: memory_save is called SEPARATELY after response is sent (async)
    
    Args:
        user_message: The user's chat message
        user_id: Authenticated user ID
        reasoning_steps: Optional list to append reasoning info
    
    Returns:
        Tuple of (answer, used_memories, search_latency_ms)
    """
    if reasoning_steps is None:
        reasoning_steps = []
    
    # 1. Search for relevant memories
    reasoning_steps.append(ReasoningStep(
        step="memory_search", 
        detail=f"Searching memories for: {user_message[:50]}..."
    ))
    
    search_result = memory_search(user_message, user_id=user_id, limit=5)
    memories = search_result.get("memories", [])
    latency_ms = search_result.get("latency_ms", 0)
    
    reasoning_steps.append(ReasoningStep(
        step="memory_result", 
        detail=f"Found {len(memories)} relevant memories in {latency_ms:.1f}ms"
    ))
    
    # 2. Build context-aware prompt
    memories_context = format_memories_context(memories)
    
    prompt = f"""You are a helpful assistant. 

{memories_context}

User: {user_message}

Respond naturally. If the memories are relevant, use them to personalize your response.
If they are not relevant, just answer the question directly."""

    # 3. Generate response
    reasoning_steps.append(ReasoningStep(step="llm_call", detail="Generating response with memory context"))
    
    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        answer = getattr(response, "content", None) or str(response)
    except Exception as e:
        reasoning_steps.append(ReasoningStep(step="error", detail=f"LLM call failed: {e}"))
        answer = "I'm sorry, I couldn't process your request right now."
    
    return answer, memories, latency_ms


def save_conversation_memory(
    user_id: int,
    user_message: str,
    assistant_response: str,
    metadata: dict | None = None,
) -> None:
    """
    Save conversation as a memory (called async after response).
    
    Creates a memory entry combining the user message and response
    for future retrieval.
    """
    # Format conversation for memory storage
    memory_text = f"User asked: {user_message}. Assistant responded: {assistant_response[:200]}"
    
    full_metadata = {
        "type": "conversation",
        "user_message": user_message,
        **(metadata or {}),
    }
    
    memory_save(user_id, memory_text, full_metadata, scope="user")
