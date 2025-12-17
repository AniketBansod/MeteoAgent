from fastapi import FastAPI
from pydantic import BaseModel
import traceback
import logging

from app.agent import get_agent

app = FastAPI(title="MeteoAgent")


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat(req: ChatRequest):
    if not req.message.strip():
        return {
            "answer": None,
            "reasoning_steps": [],
            "error": "Please enter a valid question."
        }

    executor, reasoning_steps = get_agent()

    try:
        response = executor(req.message)
        return {
            "answer": response,
            "reasoning_steps": reasoning_steps,
            "error": None
        }

    except Exception as e:
        logging.exception("Chat error")
        return {
            "answer": None,
            "reasoning_steps": reasoning_steps,
            "error": "Internal error",
            "debug": {
                "exception": str(e),
                "trace": traceback.format_exc()
            }
        }


@app.get("/debug/env")
def debug_env():
    import os
    return {
        "OPENROUTER_API_KEY_set": bool(os.getenv("OPENROUTER_API_KEY")),
        "WEATHER_API_KEY_set": bool(os.getenv("WEATHER_API_KEY"))
    }
