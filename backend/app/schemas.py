from pydantic import BaseModel
from typing import List, Optional


class IntentResult(BaseModel):
    intent: str
    cities: List[str]
    confidence: float
    is_multi_city: bool = False


class ReasoningStep(BaseModel):
    step: str
    detail: Optional[str] = None


class AgentResponse(BaseModel):
    answer: Optional[str]
    reasoning: List[ReasoningStep]
    intent: str
    cities: List[str]
    confidence: float
    error: Optional[str]
