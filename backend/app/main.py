from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="MeteoAgent")

class ChatRequest(BaseModel):
    message: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: ChatRequest):
    return {
        "answer": "MeteoAgent backend is running.",
        "reasoning_steps": ["Health check response"],
        "error": None
    }
