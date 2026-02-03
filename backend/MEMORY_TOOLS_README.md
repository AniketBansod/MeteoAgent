# Memory Tools Implementation

## Overview

This implementation adds `memory_save` and `memory_search` tools for the weather chat app using **txtai** for semantic search and **PostgreSQL** for persistent storage.

## Architecture

```
User sends chat message
        │
        ▼
┌───────────────────────────────┐
│   1. memory_search (SYNC)     │
│   - txtai semantic search     │
│   - Returns k relevant entries│
│   - ~10ms latency             │
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│   2. LLM Context Building     │
│   - User message              │
│   - Relevant past memories    │
│   - Generate response         │
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│   3. Response to Client       │
│   (IMMEDIATE)                 │
└───────────────────────────────┘
        │
        ▼ (ASYNC/PARALLEL)
┌───────────────────────────────┐
│   4. memory_save (BACKGROUND) │
│   - Insert into Postgres      │
│   - Upsert txtai index        │
│   - NO full rebuild           │
│   - Immediately searchable    │
└───────────────────────────────┘
```

## Key Files Modified

### 1. `app/db_init.py`
- Creates `memories` table with user_id, scope, text, metadata (JSONB)

### 2. `app/memory_index.py`
- Singleton `MemoryIndex` class using txtai
- Uses `sentence-transformers/all-MiniLM-L6-v2` for embeddings
- Incremental upsert support (no full rebuild needed)
- Thread-safe operations

### 3. `app/memory_service.py`
- `search_memories()`: Semantic search → Postgres fetch
- `save_memory_async()`: Postgres insert + txtai upsert

### 4. `app/tools.py`
- `memory_search()`: Tool wrapper for semantic search
- `memory_save()`: Tool wrapper for async save
- `format_memories_context()`: Format memories for LLM prompt

### 5. `app/memory_chat_routes.py`
- `/memory/chat` endpoint implementing the full flow
- Uses `BackgroundTasks` for async memory save

## API Endpoints

### POST `/memory/chat`
Memory-aware chat with automatic conversation saving.

**Request:**
```json
{
  "message": "Do you remember where I live?"
}
```

**Response:**
```json
{
  "answer": "Yes, you live in Bangalore!",
  "used_memories": ["User lives in Bangalore", "..."],
  "latency_ms": 12.5,
  "memory_count": 2
}
```

### POST `/memory/save`
Explicitly save a memory.

**Request:**
```json
{
  "text": "I live in Bangalore",
  "metadata": {"category": "location"},
  "scope": "user"
}
```

### POST `/memory/search`
Search memories without chat.

**Request:**
```json
{
  "query": "where do I live",
  "limit": 5
}
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize database:
```python
from app.db_init import init_db
init_db()  # Creates users + memories tables
```

3. Start server:
```bash
uvicorn app.main:app --reload
```

## Environment Variables

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=meteo
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
OPENROUTER_API_KEY=your_key
```

## Performance

- **Search latency**: ~10ms (txtai in-memory)
- **Save latency**: ~50ms (Postgres + index upsert)
- **Index size**: Tested with 1000+ memories

## Inspired By

The txtai integration follows patterns from `mem_search.ipynb`:
- Same embedding model (`all-MiniLM-L6-v2`)
- Content storage enabled for full text retrieval
- Incremental indexing without full rebuild
