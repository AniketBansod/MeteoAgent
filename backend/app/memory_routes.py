from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

from app.schemas import MemoryCreateRequest, MemorySearchRequest, MemorySearchResponse
from app.security import get_current_user_id
from app.memory_service import save_memory_async, search_memories
router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryAcceptedResponse(BaseModel):
    status: str


@router.post("/save", response_model=MemoryAcceptedResponse)
def memory_save(
    req: MemoryCreateRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
):
    background_tasks.add_task(
        save_memory_async,
        user_id,
        req.text,
        req.metadata,
        req.scope or "user",
    )

    return MemoryAcceptedResponse(status="accepted")

@router.post("/search", response_model=MemorySearchResponse)
def memory_search(
    req: MemorySearchRequest,
    user_id: int = Depends(get_current_user_id),
):
    results, latency_ms = search_memories(req.query, user_id=user_id, limit=req.limit)
    return MemorySearchResponse(results=results, latency_ms=latency_ms)
