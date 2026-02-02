from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict


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

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

class SignupResponse(BaseModel):
    user_id: int
    email: str
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MemoryCreateRequest(BaseModel):
    text: str
    metadata: Optional[Dict] = None
    scope: Optional[str] = "user"

class MemoryCreateResponse(BaseModel):
    memory_id: int
    
class MemorySearchRequest(BaseModel):
    query: str
    limit: int = 5

class MemorySearchResult(BaseModel):
    id: int
    text: str
    metadata: dict | None
    score: float

class MemorySearchResponse(BaseModel):
    results: List[MemorySearchResult]
    latency_ms: float