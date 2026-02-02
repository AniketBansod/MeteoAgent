from txtai.embeddings import Embeddings
from app.db import get_db_connection
import threading

# Singleton lock (important for concurrency)
_lock = threading.Lock()
_instance = None


class MemoryIndex:
    def __init__(self):
        # txtai embeddings config
        self.embeddings = Embeddings({
            "path": "sentence-transformers/all-MiniLM-L6-v2",
            "content": True
        })
        self.initialized = False

    def initialize(self):
        """
        Build index from Postgres ONCE.
        Safe to call multiple times.
        """
        if self.initialized:
            return

        with _lock:
            if self.initialized:
                return

            print("🔄 Building memory index from Postgres...")

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

            self.initialized = True

            cur.close()
            conn.close()

            print(f"✅ Memory index ready ({len(data)} memories)")

    def add_memory(self, memory_id: int, text: str):
        """
        Incrementally add a single memory.
        """
        self.initialize()

        self.embeddings.upsert([
            {"id": str(memory_id), "text": text}
        ])

    def search(self, query: str, limit: int = 5):
        """
        Semantic search over memories.
        """
        self.initialize()
        return self.embeddings.search(query, limit=limit)


def get_memory_index() -> MemoryIndex:
    global _instance

    if _instance is None:
        _instance = MemoryIndex()

    return _instance
