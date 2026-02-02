from fastapi import APIRouter, Depends
from app.schemas import MemoryCreateRequest, MemoryCreateResponse, MemorySearchRequest, MemorySearchResponse, MemorySearchResult
from app.db import get_db_connection
from app.security import get_current_user_id
from app.memory_index import get_memory_index
from psycopg2.extras import Json
import time
router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/save", response_model=MemoryCreateResponse)
def memory_save(
    req: MemoryCreateRequest,
    user_id: int = Depends(get_current_user_id),
):
    conn = get_db_connection()
    cur = conn.cursor()

    # 1️⃣ Insert into Postgres (source of truth)
    cur.execute(
        """
        INSERT INTO memories (user_id, scope, text, metadata)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (
        user_id,
        req.scope,
        req.text,
        Json(req.metadata) if req.metadata else None,
        ),
    )


    memory_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    # 2️⃣ Incrementally update txtai index
    memory_index = get_memory_index()
    memory_index.add_memory(memory_id, req.text)

    return MemoryCreateResponse(memory_id=memory_id)

@router.post("/search", response_model=MemorySearchResponse)
def memory_search(
    req: MemorySearchRequest,
    user_id: int = Depends(get_current_user_id),
):
    memory_index = get_memory_index()

    # 1️⃣ Semantic search (txtai)
    start = time.perf_counter()
    hits = memory_index.search(req.query, limit=req.limit)
    latency_ms = (time.perf_counter() - start) * 1000

    if not hits:
        return MemorySearchResponse(results=[], latency_ms=latency_ms)

    memory_ids = [int(h["id"]) for h in hits]
    scores = {int(h["id"]): h["score"] for h in hits}

    # 2️⃣ Fetch full records from Postgres
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, text, metadata
        FROM memories
        WHERE id = ANY(%s) AND user_id = %s
        """,
        (memory_ids, user_id),
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = [
        {
            "id": r[0],
            "text": r[1],
            "metadata": r[2],
            "score": scores.get(r[0], 0.0),
        }
        for r in rows
    ]

    # Preserve semantic ranking order
    results.sort(key=lambda r: r["score"], reverse=True)

    return MemorySearchResponse(
        results=results,
        latency_ms=latency_ms,
    )
