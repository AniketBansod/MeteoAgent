from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

import os

from langchain_openai import ChatOpenAI

from app.memory_service import search_memories, save_memory_async
from app.security import get_current_user_id
from app.tools import format_memories_context


router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryChatRequest(BaseModel):
    message: str


class MemoryChatResponse(BaseModel):
    answer: str
    used_memories: list[str]
    latency_ms: float
    memory_count: int


def _get_memory_chat_llm() -> ChatOpenAI:
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


@router.post("/chat", response_model=MemoryChatResponse)
def memory_chat(
    req: MemoryChatRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
):
    """
    Memory-aware chat endpoint implementing the expected flow:
    
    1. User sends chat message
    2. memory_search called -> search for related info using txtai
    3. LLM builds context (user message + relevant memories)
    4. Response sent to client (IMMEDIATE)
    5. ASYNC: Save conversation to Postgres + update txtai index
    
    The memory is immediately searchable after save (incremental upsert).
    """
    query = (req.message or "").strip()
    if not query:
        return MemoryChatResponse(
            answer="Please enter a valid message.",
            used_memories=[],
            latency_ms=0,
            memory_count=0,
        )

    # ========================================
    # STEP 1: Memory Search (txtai semantic)
    # ========================================
    top_k = 5
    results, latency_ms = search_memories(query, user_id=user_id, limit=top_k)
    used_memories = [r.get("text") for r in (results or []) if r.get("text")][:top_k]

    # ========================================
    # STEP 2: Build Context-Aware Prompt
    # ========================================
    memories_context = format_memories_context(used_memories)
    
    prompt = f"""---- PROMPT START ----
System:
You are a helpful assistant. The following are memories from the user's past conversations.
Use them only if they are relevant to answering the user's question.
Do not mention tools or weather unless explicitly asked.

{memories_context}

User:
{query}
---- PROMPT END ----"""

    # ========================================
    # STEP 3: LLM Generates Response
    # ========================================
    try:
        llm = _get_memory_chat_llm()
        res = llm.invoke(prompt)
        answer = getattr(res, "content", None) or str(res)
    except Exception as e:
        print(f"memory_chat LLM call failed: {e}")
        answer = "Unable to process request right now."

    # ========================================
    # STEP 4: Return Response to Client (IMMEDIATE)
    # ========================================
    # Response is sent NOW, before memory save completes
    
    # ========================================
    # STEP 5: ASYNC Memory Save (Background)
    # ========================================
    # Save conversation as memory for future retrieval
    # This runs AFTER the response is sent to the client
    
    memory_text = f"User asked: {query}. Assistant responded: {answer[:300]}"
    metadata = {
        "type": "conversation",
        "user_message": query,
    }
    
    background_tasks.add_task(
        save_memory_async,
        user_id,
        memory_text,
        metadata,
        "user",  # scope
    )

    return MemoryChatResponse(
        answer=answer,
        used_memories=used_memories,
        latency_ms=latency_ms,
        memory_count=len(used_memories),
    )
