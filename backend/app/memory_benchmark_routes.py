from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.memory_service import search_memories
from app.security import get_current_user_id


router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryBenchmarkRequest(BaseModel):
    query: str
    runs: int = 10


@router.post("/benchmark")
def memory_benchmark(
    req: MemoryBenchmarkRequest,
    user_id: int = Depends(get_current_user_id),
):
    query = (req.query or "").strip()
    runs = int(req.runs or 0)

    if not query:
        return {"avg_latency_ms": 0.0, "min_latency_ms": 0.0, "max_latency_ms": 0.0, "runs": 0}

    if runs <= 0:
        runs = 10

    latencies: list[float] = []

    for _ in range(runs):
        _, latency_ms = search_memories(query, user_id=user_id, limit=5)
        latencies.append(float(latency_ms))

    avg_latency_ms = sum(latencies) / len(latencies)
    min_latency_ms = min(latencies)
    max_latency_ms = max(latencies)

    return {
        "avg_latency_ms": avg_latency_ms,
        "min_latency_ms": min_latency_ms,
        "max_latency_ms": max_latency_ms,
        "runs": len(latencies),
    }
