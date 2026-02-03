from __future__ import annotations

import time
import threading
from typing import Any

from app.db import get_db_connection
from app.memory_index import get_memory_index
from psycopg2.extras import Json


_save_lock = threading.Lock()


def search_memories(query: str, user_id: int, limit: int = 5) -> tuple[list[dict[str, Any]], float]:
    """
    Search memories using txtai semantic search, then fetch full records from Postgres.
    
    Flow:
    1. txtai searches in-memory index (fast, ~10ms)
    2. Returns memory IDs with scores
    3. Fetch full records from Postgres filtered by user_id
    4. Return results sorted by semantic relevance
    
    Args:
        query: Search query string
        user_id: Filter memories by this user
        limit: Max results to return
    
    Returns:
        Tuple of (results_list, latency_ms)
    """
    memory_index = get_memory_index()

    # 1️⃣ Semantic search (txtai) - measures latency
    start = time.perf_counter()
    hits = memory_index.search(query, limit=limit * 2)  # Get more for user filter
    latency_ms = (time.perf_counter() - start) * 1000

    if not hits:
        return [], latency_ms

    # Extract IDs and scores
    memory_ids = []
    scores = {}
    for h in hits:
        try:
            mid = int(h["id"])
            memory_ids.append(mid)
            scores[mid] = h["score"]
        except (ValueError, KeyError):
            continue

    if not memory_ids:
        return [], latency_ms

    # 2️⃣ Fetch full records from Postgres (filtered by user_id)
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

    # Apply final limit after user filtering
    return results[:limit], latency_ms


def save_memory_async(
    user_id: int,
    text: str,
    metadata: dict | None = None,
    scope: str = "user",
) -> int | None:
    """
    Save memory to Postgres and incrementally update txtai index.
    
    This function is designed to be called as a background task
    AFTER the response is sent to the user.
    
    Flow:
    1. Insert into Postgres memories table
    2. Upsert into txtai index (incremental, no full rebuild)
    
    Thread-safe via lock to avoid concurrent index mutations.
    
    Args:
        user_id: User who owns this memory
        text: Memory content
        metadata: Optional metadata dict (stored as JSONB)
        scope: Memory scope ("user" or "org")
    
    Returns:
        memory_id if successful, None otherwise
    """
    try:
        clean_text = (text or "").strip()
        if not clean_text:
            return None

        # 1️⃣ Insert into Postgres
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO memories (user_id, scope, text, metadata)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (
                user_id,
                scope,
                clean_text,
                Json(metadata) if metadata else None,
            ),
        )
        memory_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        # 2️⃣ Incrementally update txtai index (thread-safe)
        memory_index = get_memory_index()
        with _save_lock:
            memory_index.add_memory(memory_id, clean_text)

        print(f"✅ Memory saved: id={memory_id}, user={user_id}")
        return memory_id

    except Exception as e:
        print(f"❌ save_memory_async failed: {e}")
        return None
