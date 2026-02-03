"""Seed the Postgres `memories` table with real-world text and warm the txtai in-memory index.

Default source is Simple Wikipedia via HuggingFace `datasets`.

Usage:
  python -m app.seed_memories --n 1000 --email seed@example.com

Notes:
- Inserts rows into Postgres (mandatory)
- Upserts into txtai in-memory index (incremental; no full rebuild required)
"""

from __future__ import annotations

import argparse
import os
from typing import Any

from dotenv import load_dotenv
from psycopg2.extras import Json, execute_values

from app.db import get_db_connection
from app.memory_index import get_memory_index


def _ensure_user(email: str, password: str) -> int:
    """Ensure a user exists and return user_id.

    Uses the same password hashing as the app signup flow so the user can log in.
    """
    from app.security import hash_password

    email = (email or "").strip().lower()
    if not email:
        raise ValueError("email is required")
    if not password:
        raise ValueError("password is required")

    pw_hash = hash_password(password)

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO users (email, password_hash)
        VALUES (%s, %s)
        ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash
        RETURNING id
        """,
        (email, pw_hash),
    )
    user_id = int(cur.fetchone()[0])

    conn.commit()
    cur.close()
    conn.close()

    return user_id


def _load_simple_wikipedia_texts(n: int, max_chars: int) -> list[dict[str, Any]]:
    """Load up to n text snippets from Simple Wikipedia."""
    from datasets import load_dataset

    dataset = load_dataset("rahular/simple-wikipedia")

    out: list[dict[str, Any]] = []
    for ex in dataset["train"]:
        text = (ex.get("text") or "").strip()
        if not text:
            continue

        # Keep payload reasonably sized for embedding + storage
        if len(text) > max_chars:
            text = text[:max_chars].rsplit(" ", 1)[0] + "..."

        title = (ex.get("title") or "").strip()
        meta = {
            "source": "rahular/simple-wikipedia",
            "title": title,
        }

        out.append({"text": text, "metadata": meta})
        if len(out) >= n:
            break

    return out


def seed_memories(
    *,
    user_id: int | None = None,
    email: str | None = None,
    password: str | None = None,
    n: int = 1000,
    scope: str = "user",
    max_chars: int = 400,
    batch_size: int = 200,
) -> dict[str, Any]:
    load_dotenv()

    if user_id is None:
        user_id = _ensure_user(email or "seed@example.com", password or "seed-password")

    items = _load_simple_wikipedia_texts(n=n, max_chars=max_chars)
    if not items:
        raise RuntimeError("No texts loaded from dataset")

    conn = get_db_connection()
    cur = conn.cursor()

    inserted_ids: list[int] = []
    inserted_docs: list[dict[str, str]] = []

    # Insert in batches and upsert into txtai incrementally.
    memory_index = get_memory_index()

    for i in range(0, len(items), batch_size):
        chunk = items[i : i + batch_size]
        values = [
            (
                user_id,
                scope,
                c["text"],
                Json(c.get("metadata") or None),
            )
            for c in chunk
        ]

        # Fetch inserted ids so we can upsert into txtai without rebuild.
        rows = execute_values(
            cur,
            """
            INSERT INTO memories (user_id, scope, text, metadata)
            VALUES %s
            RETURNING id
            """,
            values,
            fetch=True,
        )

        chunk_ids = [int(r[0]) for r in rows]
        inserted_ids.extend(chunk_ids)

        docs = [{"id": str(mid), "text": chunk[j]["text"]} for j, mid in enumerate(chunk_ids)]
        inserted_docs.extend(docs)

        # Update in-memory txtai index immediately (no restart)
        memory_index.upsert_many(docs)

    conn.commit()
    cur.close()
    conn.close()

    return {
        "user_id": user_id,
        "inserted": len(inserted_ids),
        "first_id": inserted_ids[0] if inserted_ids else None,
        "last_id": inserted_ids[-1] if inserted_ids else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Seed memories with real-world text and warm txtai index")
    parser.add_argument("--user-id", type=int, default=None, help="Seed memories for an existing user_id")
    parser.add_argument("--email", default=os.getenv("SEED_EMAIL", "seed@example.com"), help="Email to create/update if --user-id not provided")
    parser.add_argument("--password", default=os.getenv("SEED_PASSWORD", "seed-password"), help="Password for created/updated user")
    parser.add_argument("--n", type=int, default=int(os.getenv("SEED_N", "1000")))
    parser.add_argument("--scope", default=os.getenv("SEED_SCOPE", "user"))
    parser.add_argument("--max-chars", type=int, default=int(os.getenv("SEED_MAX_CHARS", "400")))
    parser.add_argument("--batch-size", type=int, default=int(os.getenv("SEED_BATCH_SIZE", "200")))

    args = parser.parse_args()

    res = seed_memories(
        user_id=args.user_id,
        email=args.email,
        password=args.password,
        n=args.n,
        scope=args.scope,
        max_chars=args.max_chars,
        batch_size=args.batch_size,
    )

    print("✅ Seed complete")
    print(res)


if __name__ == "__main__":
    main()
