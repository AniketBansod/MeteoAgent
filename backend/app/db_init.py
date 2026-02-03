from app.db import get_db_connection

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT now()
    );
    """)

    # Memories table for txtai-powered semantic search
    cur.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        scope TEXT DEFAULT 'user',
        text TEXT NOT NULL,
        metadata JSONB,
        created_at TIMESTAMP DEFAULT now()
    );
    """)

    # Index for fast user_id lookups
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database tables ready (users, memories)")
