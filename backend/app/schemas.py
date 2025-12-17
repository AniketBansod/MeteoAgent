from pydantic import BaseModel
from typing import List


class IntentResult(BaseModel):
    intent: str
    cities: List[str]
    confidence: float
