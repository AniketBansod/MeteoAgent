from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback
import logging

from app.agent import get_agent
from app.intent import detect_intent
from app.tools import get_weather_json, compare_weather, score_city, summarize_forecast, weekend_summary, tomorrow_summary, hourly_lookup
from app.schemas import AgentResponse, ReasoningStep

app = FastAPI(title="MeteoAgent")

# Enable permissive CORS for production compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str


class WeatherBatchRequest(BaseModel):
    cities: list[str]


@app.post("/chat", response_model=AgentResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        return AgentResponse(
            answer=None,
            reasoning=[],
            intent="unknown",
            cities=[],
            confidence=0.0,
            error="Please enter a valid question.",
        )

    intent = detect_intent(req.message)
    reasoning_steps = [
        ReasoningStep(step="intent_detection", detail=f"Intent={intent.intent}, Cities={intent.cities}, Multi={intent.is_multi_city}")
    ]

    # Comparison intent: require at least two cities, fetch each and score
    if intent.intent == "comparison":
        if len(intent.cities) < 2:
            return AgentResponse(
                answer="Please provide at least two cities to compare.",
                reasoning=reasoning_steps,
                intent=intent.intent,
                cities=intent.cities,
                confidence=intent.confidence,
                error=None,
            )
        weather_list = []
        for city in intent.cities:
            try:
                w = get_weather_json(city)
                if w:
                    weather_list.append(w)
                    reasoning_steps.append(ReasoningStep(step="tool_result", detail=f"Weather received for {city}"))
                else:
                    reasoning_steps.append(ReasoningStep(step="error", detail=f"No weather for {city}"))
            except Exception as e:
                reasoning_steps.append(ReasoningStep(step="error", detail=f"Failed for {city}: {str(e)}"))

        if len(weather_list) < 2:
            return AgentResponse(
                answer="Unable to compare due to missing weather data.",
                reasoning=reasoning_steps,
                intent=intent.intent,
                cities=intent.cities,
                confidence=intent.confidence,
                error=None,
            )

        # Score each city and pick winner
        scored = [(w, score_city(w)) for w in weather_list]
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[0]
        # If tie, declare both equal
        winners = [w[0]["city"] for w in scored if w[1] == top[1]]
        if len(winners) == 1:
            winner = winners[0]
        else:
            winner = "Both equal"

        # Build human-readable answer comparing first two prominent cities
        a = weather_list[0]
        b = weather_list[1]
        answer = (
            f"{winner} looks better for travel right now.\n\n"
            f"Temperature: {a['city']} {a['temp']}°C vs {b['city']} {b['temp']}°C\n"
            f"Humidity: {a['city']} {a['humidity']}% vs {b['city']} {b['humidity']}%\n"
            f"Wind: {a['city']} {a['wind_kmh']} km/h vs {b['city']} {b['wind_kmh']} km/h\n"
        )

        return AgentResponse(
            answer=answer,
            reasoning=reasoning_steps,
            intent=intent.intent,
            cities=intent.cities,
            confidence=intent.confidence,
            error=None,
        )

    # Forecast intent: route to appropriate summarizer
    if intent.intent == "forecast":
        if not intent.cities:
            return AgentResponse(
                answer="Please specify a city for the forecast.",
                reasoning=reasoning_steps,
                intent=intent.intent,
                cities=intent.cities,
                confidence=intent.confidence,
                error=None,
            )

        def summarize_for_message(city: str):
            t = intent
            msg = req.message.lower()
            if "weekend" in msg:
                return weekend_summary(city)
            if "tomorrow" in msg:
                return tomorrow_summary(city)
            # hour extraction: e.g., 6pm, 18:00
            import re
            m = re.search(r"\b(\d{1,2})(?:\s*(am|pm))\b", msg)
            if m:
                hr = int(m.group(1))
                ap = (m.group(2) or "").lower()
                if ap == "pm" and hr < 12:
                    hr += 12
                return hourly_lookup(city, hr)
            m = re.search(r"\b(\d{1,2}):(\d{2})\b", msg)
            if m:
                hr = int(m.group(1))
                return hourly_lookup(city, hr)
            return summarize_forecast(city)

        summaries = []
        for city in intent.cities:
            res = summarize_for_message(city)
            if isinstance(res, dict) and res.get("summary"):
                summaries.append(f"{res.get('city', city)}: {res['summary']}")
                reasoning_steps.append(ReasoningStep(step="tool_result", detail=f"Forecast summarized for {city}"))
            else:
                reasoning_steps.append(ReasoningStep(step="error", detail=f"Forecast unavailable for {city}"))

        return AgentResponse(
            answer="\n".join(summaries) if summaries else "Forecast unavailable.",
            reasoning=reasoning_steps,
            intent=intent.intent,
            cities=intent.cities,
            confidence=intent.confidence,
            error=None,
        )

    # Direct route for current weather with cities
    if intent.intent == "current_weather":
        if not intent.cities:
            return AgentResponse(
                answer="Please specify a city.",
                reasoning=reasoning_steps,
                intent=intent.intent,
                cities=intent.cities,
                confidence=intent.confidence,
                error=None,
            )
        # If multiple cities are provided, behave like comparison using scores
        if len(intent.cities) >= 2:
            weather_list = []
            for city in intent.cities:
                try:
                    w = get_weather_json(city)
                    if w:
                        weather_list.append(w)
                        reasoning_steps.append(ReasoningStep(step="tool_result", detail=f"Weather received for {city}"))
                    else:
                        reasoning_steps.append(ReasoningStep(step="error", detail=f"No weather for {city}"))
                except Exception as e:
                    reasoning_steps.append(ReasoningStep(step="error", detail=f"Failed for {city}: {str(e)}"))
            if len(weather_list) < 2:
                return AgentResponse(
                    answer="Unable to compare due to missing weather data.",
                    reasoning=reasoning_steps,
                    intent=intent.intent,
                    cities=intent.cities,
                    confidence=intent.confidence,
                    error=None,
                )
            a = weather_list[0]; b = weather_list[1]
            answer = (
                f"Comparison summary:\n"
                f"Temperature: {a['city']} {a['temp']}°C vs {b['city']} {b['temp']}°C\n"
                f"Humidity: {a['city']} {a['humidity']}% vs {b['city']} {b['humidity']}%\n"
                f"Wind: {a['city']} {a['wind_kmh']} km/h vs {b['city']} {b['wind_kmh']} km/h\n"
            )
            return AgentResponse(
                answer=answer,
                reasoning=reasoning_steps,
                intent=intent.intent,
                cities=intent.cities,
                confidence=intent.confidence,
                error=None,
            )
        # Single city
        city = intent.cities[0]
        try:
            w = get_weather_json(city)
            return AgentResponse(
                answer=(
                    f"{w['city']}: {w['temp']}°C (feels {w['feels']}°C), "
                    f"humidity {w['humidity']}%, wind {w['wind_kmh']} km/h, {w['condition']}"
                ) if w else None,
                reasoning=reasoning_steps,
                intent=intent.intent,
                cities=intent.cities,
                confidence=intent.confidence,
                error=None if w else "Unable to fetch weather right now.",
            )
        except Exception as e:
            logging.exception("Weather tool error")
            reasoning_steps.append(ReasoningStep(step="error", detail=f"Weather fetch failed for {city}: {str(e)}"))
            return AgentResponse(
                answer=None,
                reasoning=reasoning_steps,
                intent=intent.intent,
                cities=intent.cities,
                confidence=intent.confidence,
                error="Unable to fetch weather right now.",
            )

    # Unknown intent: friendly guidance
    if intent.intent == "unknown":
        return AgentResponse(
            answer="I can help with weather-related questions.",
            reasoning=reasoning_steps,
            intent=intent.intent,
            cities=intent.cities,
            confidence=intent.confidence,
            error=None,
        )

    # For other intents, use the LLM agent
    agent, agent_steps = get_agent()
    reasoning_steps.extend(agent_steps)

    try:
        response = agent.run(req.message)
        reasoning_steps.append(ReasoningStep(step="final_answer", detail="Answer generated successfully"))
        return AgentResponse(
            answer=response,
            reasoning=reasoning_steps,
            intent=intent.intent,
            cities=intent.cities,
            confidence=intent.confidence,
            error=None,
        )

    except Exception as e:
        logging.exception("Chat error")
        reasoning_steps.append(ReasoningStep(step="error", detail=str(e)))
        return AgentResponse(
            answer=None,
            reasoning=reasoning_steps,
            intent=intent.intent,
            cities=intent.cities,
            confidence=intent.confidence,
            error="Unable to process request.",
        )


@app.get("/debug/env")
def debug_env():
    import os
    return {
        "OPENROUTER_API_KEY_set": bool(os.getenv("OPENROUTER_API_KEY")),
        "WEATHER_API_KEY_set": bool(os.getenv("WEATHER_API_KEY"))
    }


@app.get("/weather")
def get_weather(city: str):
    """Return structured weather for a single city.
    Frontend uses this for rendering multi-city results.
    """
    if not city or not city.strip():
        raise HTTPException(status_code=400, detail="Missing 'city' query param")
    data = get_weather_json(city.strip())
    if not data:
        raise HTTPException(status_code=404, detail="Weather unavailable")
    return data


@app.post("/weather/batch")
def get_weather_batch(req: WeatherBatchRequest):
    """Return structured weather for a list of cities (best-effort)."""
    if not req.cities:
        return []
    out = []
    seen = set()
    for c in req.cities:
        name = (c or "").strip()
        if not name:
            continue
        if name.lower() in seen:
            continue
        seen.add(name.lower())
        w = get_weather_json(name)
        if w:
            out.append(w)
    return out
