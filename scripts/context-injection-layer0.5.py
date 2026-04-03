#!/usr/bin/env python3
"""
Layer 0.5: Pre-Turn Context Injection

Runs before each turn (or via cron every 15min), queries Qdrant for semantically
relevant memories, and injects them into the current turn context.

This is a *proto-integration* — designed to be called from:
  1. OpenClaw plugin/hook (pre-turn, automatic)
  2. Cron job (background, every 15min)
  3. Manual CLI (for testing)

Usage:
  python3 context-injection-layer0.5.py --query "question" --collection memory_self
  python3 context-injection-layer0.5.py --auto-inject  # Run on recent messages

Architecture:
  - Queries Qdrant (5 collections: self, projects, lessons, daily, semantic)
  - Scores results (threshold 0.3)
  - Ranks by semantic relevance + recency
  - Formats as structured context block (JSON + markdown)
  - Returns injection payload ready for pre-turn insertion

Output format (ready for OpenClaw context injection):
  {
    "injection_type": "semantic_memory",
    "confidence": 0.XX,
    "timestamp": "ISO-8601",
    "relevant_memories": [
      {"source_file": "...", "chunk_idx": 0, "score": 0.XX, "text": "..."}
    ],
    "context_markdown": "# Relevant Memories\n..."
  }
"""

import os, sys, json, re, subprocess
from datetime import datetime, timedelta
from pathlib import Path

QDRANT_URL = "http://172.17.0.1:6333"
WORKSPACE = Path("/data/.openclaw/workspace")

# ── Helpers ──────────────────────────────────────────────────────────────────

def http_post_json(url, body):
    import urllib.request
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

def embed_query(query_text):
    """Embed a query string via OpenAI."""
    import urllib.request
    key = os.environ.get("OPENAI_API_KEY", "")
    req = urllib.request.Request(
        "https://api.openai.com/v1/embeddings",
        data=json.dumps({"input": query_text, "model": "text-embedding-3-small"}).encode(),
        method="POST"
    )
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    r = urllib.request.urlopen(req)
    data = json.loads(r.read())
    return data["data"][0]["embedding"]

def search_qdrant(query_vec, collections=None, top_k=3, score_threshold=0.3):
    """Search multiple Qdrant collections."""
    if not collections:
        collections = ["memory_self", "memory_projects", "memory_lessons", "memory_daily", "memory_semantic"]
    
    results = []
    for col in collections:
        url = f"{QDRANT_URL}/collections/{col}/points/search"
        body = {
            "vector": query_vec,
            "limit": top_k,
            "with_payload": True,
            "score_threshold": score_threshold
        }
        try:
            resp = http_post_json(url, body)
            for r in resp.get("result", []):
                r["_collection"] = col
                results.append(r)
        except Exception as e:
            print(f"  ⚠ Search error in {col}: {e}", file=sys.stderr)
    
    return results

def rank_by_recency(results):
    """Boost score by recency (recent daily memories higher)."""
    now = datetime.now()
    for r in results:
        payload = r.get("payload", {})
        source = payload.get("source_file", "")
        
        # Recent daily files: boost by up to 0.2
        if "daily/" in source:
            try:
                match = re.search(r'(\d{4}-\d{2}-\d{2})', source)
                if match:
                    file_date = datetime.strptime(match.group(1), "%Y-%m-%d")
                    days_old = (now - file_date).days
                    if days_old == 0:
                        r["score"] += 0.15  # Today = +0.15
                    elif days_old <= 7:
                        r["score"] += 0.10  # This week = +0.10
                    elif days_old <= 30:
                        r["score"] += 0.05  # This month = +0.05
            except:
                pass
    
    return results

def format_context_markdown(results, max_results=5):
    """Format ranked results as human-readable markdown."""
    if not results:
        return ""
    
    results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)[:max_results]
    
    md = "# Relevant Memories (Semantic Recall)\n\n"
    for i, r in enumerate(results, 1):
        score = r.get("score", 0)
        payload = r.get("payload", {})
        source = payload.get("source_file", "?")
        chunk = payload.get("chunk_idx", "?")
        total = payload.get("total_chunks", "?")
        text = payload.get("text", "")
        col = r.get("_collection", "?")
        
        # Truncate text to 250 chars
        text_preview = (text[:250] + "...") if len(text) > 250 else text
        
        md += f"## [{i}] {source} (chunk {chunk}/{total}, score={score:.3f})\n\n"
        md += f"*From {col}*\n\n"
        md += f"```\n{text_preview}\n```\n\n"
    
    return md

# ── Query mode (CLI) ────────────────────────────────────────────────────────

if "--query" in sys.argv:
    idx = sys.argv.index("--query")
    query_text = " ".join(sys.argv[idx+1:])
    
    print(f"[Layer 0.5] Embedding query: \"{query_text[:80]}...\"", file=sys.stderr)
    query_vec = embed_query(query_text)
    
    print(f"[Layer 0.5] Searching Qdrant...", file=sys.stderr)
    results = search_qdrant(query_vec)
    results = rank_by_recency(results)
    
    print(f"[Layer 0.5] Found {len(results)} results", file=sys.stderr)
    
    # Output JSON
    injection = {
        "injection_type": "semantic_memory",
        "query": query_text[:200],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "result_count": len(results),
        "relevant_memories": [
            {
                "source_file": r.get("payload", {}).get("source_file"),
                "chunk_idx": r.get("payload", {}).get("chunk_idx"),
                "score": r.get("score"),
                "collection": r.get("_collection"),
                "text": r.get("payload", {}).get("text")
            }
            for r in sorted(results, key=lambda x: x.get("score", 0), reverse=True)[:5]
        ],
        "context_markdown": format_context_markdown(results, max_results=5)
    }
    
    print(json.dumps(injection, indent=2))
    sys.exit(0)

# ── Auto-inject mode (hook into current turn) ────────────────────────────────

if "--auto-inject" in sys.argv:
    # This would be called by OpenClaw before handling a turn.
    # For now, it's a stub that demonstrates the flow.
    
    print("[Layer 0.5] Auto-inject mode (stub)", file=sys.stderr)
    print("[Layer 0.5] In production, this would:")
    print("  1. Fetch current user message from SESSION-STATE.md or inbound metadata")
    print("  2. Generate query from that message")
    print("  3. Retrieve semantic context")
    print("  4. Inject into turn context before processing")
    
    # Placeholder: demonstrate with a dummy query
    query = "What is my current priority and recent context?"
    print(f"\n[Layer 0.5] Demo query: \"{query}\"", file=sys.stderr)
    
    query_vec = embed_query(query)
    results = search_qdrant(query_vec, top_k=5)
    results = rank_by_recency(results)
    
    injection = {
        "injection_type": "semantic_memory",
        "query": query,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "result_count": len(results),
        "relevant_memories": [
            {
                "source_file": r.get("payload", {}).get("source_file"),
                "chunk_idx": r.get("payload", {}).get("chunk_idx"),
                "score": r.get("score"),
                "text_preview": r.get("payload", {}).get("text", "")[:150]
            }
            for r in sorted(results, key=lambda x: x.get("score", 0), reverse=True)[:3]
        ]
    }
    
    print(f"\nInjection payload (for context layer):")
    print(json.dumps(injection, indent=2))
    sys.exit(0)

# ── Default: show help ──────────────────────────────────────────────────────

print(__doc__)
print("Examples:")
print("  python3 context-injection-layer0.5.py --query \"your question\"")
print("  python3 context-injection-layer0.5.py --query \"your question\" --collection memory_self")
print("  python3 context-injection-layer0.5.py --auto-inject")
