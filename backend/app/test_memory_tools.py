#!/usr/bin/env python3
"""
Test script for memory tools implementation.
Run from backend directory: python -m app.test_memory_tools
"""

import os
import sys
import time

# Ensure we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def test_db_connection():
    """Test PostgreSQL connection."""
    print("\n=== Test 1: Database Connection ===")
    from app.db import get_db_connection
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        cur.close()
        conn.close()
        print(f"✅ Database connection OK: {result}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_init_db():
    """Test database initialization."""
    print("\n=== Test 2: Initialize Database ===")
    from app.db_init import init_db
    try:
        init_db()
        print("✅ Database tables created/verified")
        return True
    except Exception as e:
        print(f"❌ Database init failed: {e}")
        return False


def test_memory_index():
    """Test txtai memory index initialization."""
    print("\n=== Test 3: Memory Index ===")
    from app.memory_index import get_memory_index
    try:
        idx = get_memory_index()
        idx.initialize()
        print(f"✅ Memory index initialized: {idx.get_doc_count()} docs")
        return True
    except Exception as e:
        print(f"❌ Memory index failed: {e}")
        return False


def test_memory_save(user_id: int = 1):
    """Test saving a memory."""
    print("\n=== Test 4: Memory Save ===")
    from app.memory_service import save_memory_async
    try:
        # Save test memories
        memories = [
            "I live in Bangalore, India",
            "My favorite programming language is Python",
            "I prefer sunny weather over rainy days",
        ]
        
        for text in memories:
            result = save_memory_async(user_id, text, {"test": True})
            print(f"  Saved: '{text[:40]}...' -> id={result}")
        
        print("✅ Memories saved successfully")
        return True
    except Exception as e:
        print(f"❌ Memory save failed: {e}")
        return False


def test_memory_search(user_id: int = 1):
    """Test searching memories."""
    print("\n=== Test 5: Memory Search ===")
    from app.memory_service import search_memories
    
    queries = [
        "where do I live",
        "programming language preference",
        "weather preference",
    ]
    
    try:
        for query in queries:
            start = time.perf_counter()
            results, latency = search_memories(query, user_id=user_id, limit=3)
            elapsed = (time.perf_counter() - start) * 1000
            
            print(f"\n  Query: '{query}'")
            print(f"  Latency: {latency:.2f}ms (total: {elapsed:.2f}ms)")
            print(f"  Results: {len(results)}")
            
            for r in results:
                print(f"    [{r['score']:.3f}] {r['text'][:60]}...")
        
        print("\n✅ Memory search working")
        return True
    except Exception as e:
        print(f"❌ Memory search failed: {e}")
        return False


def test_memory_tools():
    """Test the memory tools functions."""
    print("\n=== Test 6: Memory Tools API ===")
    from app.tools import memory_search, memory_save, format_memories_context
    
    user_id = 1
    
    try:
        # Test search tool
        result = memory_search("where do I live", user_id=user_id, limit=3)
        print(f"  memory_search result: {result['count']} memories in {result['latency_ms']:.2f}ms")
        
        # Test format
        context = format_memories_context(result['memories'])
        print(f"  format_memories_context:\n{context[:200]}...")
        
        # Test save tool
        save_result = memory_save(user_id, "This is a test memory from tools", {"source": "test"})
        print(f"  memory_save result: {save_result}")
        
        print("\n✅ Memory tools working")
        return True
    except Exception as e:
        print(f"❌ Memory tools failed: {e}")
        return False


def run_all_tests():
    """Run all tests in sequence."""
    print("=" * 60)
    print("  MEMORY TOOLS TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Need user in DB for foreign key
    from app.db import get_db_connection
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (id, email, password_hash)
        VALUES (1, 'test@example.com', 'hash')
        ON CONFLICT (id) DO NOTHING
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Test user created/verified")
    
    results.append(("Database Connection", test_db_connection()))
    results.append(("Initialize DB", test_init_db()))
    results.append(("Memory Index", test_memory_index()))
    results.append(("Memory Save", test_memory_save()))
    
    # Small delay to ensure index is updated
    time.sleep(0.5)
    
    results.append(("Memory Search", test_memory_search()))
    results.append(("Memory Tools", test_memory_tools()))
    
    print("\n" + "=" * 60)
    print("  TEST RESULTS")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\n  Total: {passed_count}/{total_count} tests passed")
    
    return all(p for _, p in results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
