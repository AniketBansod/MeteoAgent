from txtai.embeddings import Embeddings
from app.db import get_db_connection
import threading
import time

# Singleton lock (important for concurrency)
_lock = threading.Lock()
_instance = None


class MemoryIndex:
    """
    In-memory txtai index for fast semantic search over memories.
    
    Architecture inspired by mem_search.ipynb:
    - Uses sentence-transformers/all-MiniLM-L6-v2 for embeddings
    - Stores content for full text retrieval
    - Supports incremental upsert without full rebuild
    - Thread-safe singleton pattern
    """
    
    def __init__(self):
        # txtai embeddings config (same as mem_search.ipynb)
        self.embeddings = Embeddings({
            "path": "sentence-transformers/all-MiniLM-L6-v2",
            "content": True  # Enables full text retrieval
        })
        self.initialized = False
        self._doc_count = 0

    def initialize(self):
        """
        Build index from Postgres ONCE on startup.
        Safe to call multiple times (idempotent).
        """
        if self.initialized:
            return

        with _lock:
            if self.initialized:
                return

            print("🔄 Building memory index from Postgres...")
            start = time.perf_counter()

            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT id::text, text
                FROM memories
                ORDER BY id
            """)
            rows = cur.fetchall()

            data = [{"id": r[0], "text": r[1]} for r in rows]

            if data:
                self.embeddings.index(data)
                self._doc_count = len(data)
            else:
                # Initialize empty index so upsert works
                self.embeddings.index([{"id": "__init__", "text": "initialization placeholder"}])
                self._doc_count = 0

            self.initialized = True

            cur.close()
            conn.close()

            latency_ms = (time.perf_counter() - start) * 1000
            print(f"✅ Memory index ready ({self._doc_count} memories) in {latency_ms:.1f}ms")

    def add_memory(self, memory_id: int, text: str):
        """
        Incrementally add a single memory to the index.
        This is the key feature for async save without full rebuild.
        """
        self.initialize()

        with _lock:
            self.embeddings.upsert([
                {"id": str(memory_id), "text": text}
            ])
            self._doc_count += 1

    def upsert_many(self, docs: list[dict]):
        """Bulk upsert many documents into the in-memory index.

        Each doc must be: {"id": "<str>", "text": "..."}
        """
        if not docs:
            return

        self.initialize()

        # Ensure docs have required keys and skip placeholders
        clean_docs = []
        for d in docs:
            if not isinstance(d, dict):
                continue
            doc_id = d.get("id")
            text = (d.get("text") or "").strip()
            if not doc_id or doc_id == "__init__" or not text:
                continue
            clean_docs.append({"id": str(doc_id), "text": text})

        if not clean_docs:
            return

        with _lock:
            self.embeddings.upsert(clean_docs)
            # Best-effort doc count tracking (may overcount if ids overwrite)
            self._doc_count += len(clean_docs)

    def search(self, query: str, limit: int = 5) -> list[dict]:
        """
        Semantic search over memories.
        Returns list of {"id": str, "text": str, "score": float}
        """
        self.initialize()
        
        start = time.perf_counter()
        results = self.embeddings.search(query, limit=limit)
        latency_ms = (time.perf_counter() - start) * 1000
        
        # Filter out initialization placeholder
        results = [r for r in results if r.get("id") != "__init__"]
        
        return results
    
    def get_doc_count(self) -> int:
        """Return current number of indexed documents."""
        return self._doc_count


def get_memory_index() -> MemoryIndex:
    """
    Get or create the singleton MemoryIndex instance.
    Thread-safe lazy initialization.
    """
    global _instance

    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = MemoryIndex()

    return _instance
