#!/usr/bin/env python3
"""
embed_memory.py — Trident Phase 8a: Semantic Recall Pipeline

Reads Layer 1 memory files, generates embeddings via OpenAI text-embedding-3-small,
upserts into Qdrant collections. Run after memory updates or on a schedule.

Usage:
  python3 embed_memory.py              # Embed all memory files
  python3 embed_memory.py --dry-run   # Show what would be embedded, no writes
  python3 embed_memory.py --query "your query here"  # Test semantic search

Collections:
  memory_self      → self/, SOUL.md, MEMORY.md identity sections
  memory_projects  → projects/
  memory_lessons   → lessons/
  memory_daily     → daily/ (last 14 days only — keep it fresh)
  memory_semantic  → everything else (catch-all)
"""

import os, sys, json, hashlib, glob, re, time
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta

# ── Config ──────────────────────────────────────────────────────────────────

QDRANT_URL = "http://172.17.0.1:6333"
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIMS  = 1536
WORKSPACE   = Path("/data/.openclaw/workspace")
MEMORY_DIR  = WORKSPACE / "memory"
DRY_RUN     = "--dry-run" in sys.argv
QUERY_MODE  = "--query" in sys.argv

# Chunk size — stay well under 8192 token limit
MAX_CHARS   = 6000

# Exclusion prefixes — skip entirely
EXCLUDE_PREFIXES = [
    "node_modules/",
    "skills_backup_",
    "project-trident/",  # skill docs, not memory
    "skills/evm-wallet/node_modules/",
    "skills/api-gateway/references/",  # 100+ API stub READMEs, noise
    "projects/macro-oracle/node_modules/",
    "skills/proactive-agent/assets/",  # template assets, not our identity
]

# Explicit file allowlist for root-level files worth embedding
ROOT_ALLOWLIST = {"MEMORY.md", "SOUL.md", "USER.md", "AGENTS.md", "HEARTBEAT.md"}

# Collection routing: checked via string prefix (rel_path is forward-slash string)
ROUTING = [
    ("memory/self/",       "memory_self"),
    ("memory/projects/",   "memory_projects"),
    ("memory/lessons/",    "memory_lessons"),
    ("memory/daily/",      "memory_daily"),
    ("memory/reflections/","memory_projects"),  # reflections → projects bucket
    ("memory/layer0/",     "memory_lessons"),   # layer0 config → lessons
    ("memory/semantic/",   "memory_self"),       # semantic people/patterns → self
    ("memory/trading/",    "memory_projects"),
    ("MEMORY.md",          "memory_self"),
    ("SOUL.md",            "memory_self"),
    ("USER.md",            "memory_self"),
]
CATCH_ALL_COLLECTION = "memory_semantic"

# ── Helpers ──────────────────────────────────────────────────────────────────

def http_post(url, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

def http_put(url, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="PUT")
    req.add_header("Content-Type", "application/json")
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

def embed(texts):
    """Embed a list of strings. Returns list of float vectors."""
    req = urllib.request.Request(
        "https://api.openai.com/v1/embeddings",
        data=json.dumps({"input": texts, "model": EMBED_MODEL}).encode(),
        method="POST"
    )
    req.add_header("Authorization", f"Bearer {OPENAI_KEY}")
    req.add_header("Content-Type", "application/json")
    r = urllib.request.urlopen(req)
    data = json.loads(r.read())
    return [item["embedding"] for item in data["data"]]

def chunk_text(text, max_chars=MAX_CHARS):
    """Split text into overlapping chunks at paragraph boundaries."""
    paragraphs = re.split(r'\n{2,}', text.strip())
    chunks = []
    current = []
    current_len = 0

    for para in paragraphs:
        if current_len + len(para) > max_chars and current:
            chunks.append("\n\n".join(current))
            # Overlap: keep last paragraph
            current = [current[-1], para] if current else [para]
            current_len = sum(len(p) for p in current)
        else:
            current.append(para)
            current_len += len(para)

    if current:
        chunks.append("\n\n".join(current))

    return chunks if chunks else [text[:max_chars]]

def file_id(path, chunk_idx):
    """Stable point ID from file path + chunk index."""
    h = hashlib.md5(f"{path}::{chunk_idx}".encode()).hexdigest()
    # Qdrant needs unsigned int or UUID — use first 16 hex chars as UUID
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"

def route_file(rel_path):
    """Determine which collection a file belongs to."""
    for prefix, collection in ROUTING:
        if rel_path.startswith(prefix) or rel_path == prefix.rstrip("/"):
            return collection
    return CATCH_ALL_COLLECTION

def should_embed(path, rel_path):
    """Return True if this file should be embedded."""
    rel_str = str(rel_path)

    # Exclude noisy directories
    for prefix in EXCLUDE_PREFIXES:
        if rel_str.startswith(prefix):
            return False

    # Root-level files: only allowlisted ones
    if "/" not in rel_str:
        return rel_str in ROOT_ALLOWLIST

    # Only embed files under memory/, job-search/ core docs, projects/macro-oracle/ specs
    allowed_dirs = (
        "memory/",
        "job-search/documents/",
        "job-search/COLD_EMAIL_PLAYBOOK.md",
        "job-search/PROSPECT_LIST.md",
        "job-search/58DAY_SPRINT_PLAN.md",
        "job-search/STATUS.md",
        "job-search/OUTREACH_LOG.md",
        ".learnings/",
        "projects/macro-oracle/BACKEND_API_SPEC.md",
        "projects/macro-oracle/DATABASE_SCHEMA_SPEC.md",
        "projects/macro-oracle/README.md",
    )
    return any(rel_str.startswith(d) for d in allowed_dirs)

def is_recent_daily(rel_path, days=14):
    """For daily/ files, only embed the last N days."""
    match = re.search(r'(\d{4}-\d{2}-\d{2})', str(rel_path))
    if not match:
        return True
    try:
        file_date = datetime.strptime(match.group(1), "%Y-%m-%d")
        return datetime.now() - file_date <= timedelta(days=days)
    except:
        return True

def upsert_points(collection, points):
    """Upsert a batch of points into Qdrant."""
    url = f"{QDRANT_URL}/collections/{collection}/points"
    body = {"points": points}
    return http_put(url, body)

def search(query_text, collection="memory_semantic", top_k=5):
    """Semantic search across a collection."""
    vector = embed([query_text])[0]
    url = f"{QDRANT_URL}/collections/{collection}/points/search"
    body = {
        "vector": vector,
        "limit": top_k,
        "with_payload": True,
        "score_threshold": 0.3
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

# ── Query mode ────────────────────────────────────────────────────────────────

if QUERY_MODE:
    query_idx = sys.argv.index("--query")
    query_text = " ".join(sys.argv[query_idx+1:])
    collection_arg = None
    if "--collection" in sys.argv:
        col_idx = sys.argv.index("--collection")
        collection_arg = sys.argv[col_idx+1]

    collections_to_search = (
        [collection_arg] if collection_arg
        else ["memory_self", "memory_projects", "memory_lessons", "memory_daily", "memory_semantic"]
    )

    print(f"\n🔍 Semantic search: \"{query_text}\"\n")
    all_results = []
    for col in collections_to_search:
        try:
            results = search(query_text, collection=col, top_k=3)
            for r in results.get("result", []):
                r["_collection"] = col
                all_results.append(r)
        except Exception as e:
            print(f"  ⚠ {col}: {e}")

    # Sort by score
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)

    if not all_results:
        print("No results found.")
    else:
        for i, r in enumerate(all_results[:8], 1):
            score = r.get("score", 0)
            payload = r.get("payload", {})
            col = r.get("_collection", "?")
            print(f"[{i}] score={score:.3f} | {col} | {payload.get('source_file', '?')}")
            print(f"    chunk {payload.get('chunk_idx', '?')} of {payload.get('total_chunks', '?')}")
            print(f"    preview: {payload.get('text', '')[:200].strip()}")
            print()
    sys.exit(0)

# ── Main embedding pipeline ───────────────────────────────────────────────────

print(f"{'[DRY RUN] ' if DRY_RUN else ''}Trident Phase 8a — Memory Embedding Pipeline")
print(f"Workspace: {WORKSPACE}")
print(f"Qdrant: {QDRANT_URL}")
print(f"Model: {EMBED_MODEL} ({EMBED_DIMS} dims)\n")

# Gather all .md files
all_files = []
for path in WORKSPACE.glob("**/*.md"):
    if ".git" in path.parts:
        continue
    rel = path.relative_to(WORKSPACE)
    rel_str = str(rel)

    # Skip session-level ephemera
    if path.name in {"SESSION-STATE.md", "working-buffer.md", "PUBLISH.md"}:
        continue

    # Apply allowlist / exclusion logic
    if not should_embed(path, rel_str):
        continue

    # Daily files: only last 14 days
    if "daily" in rel_str and not is_recent_daily(rel_str):
        continue

    collection = route_file(rel_str)
    all_files.append((path, rel_str, collection))

print(f"Found {len(all_files)} files to embed\n")

# Process in batches
BATCH_SIZE = 10
total_chunks = 0
total_points = 0
errors = []

collection_batches = {}  # collection → list of points

for path, rel_str, collection in all_files:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if len(text) < 50:
            print(f"  skip (too short): {rel_str}")
            continue

        chunks = chunk_text(text)
        total_chunks += len(chunks)

        print(f"  {rel_str} → {collection} ({len(chunks)} chunk{'s' if len(chunks)>1 else ''})")

        if DRY_RUN:
            continue

        # Embed chunks (batch per file)
        vectors = embed(chunks)

        # Build Qdrant points
        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            points.append({
                "id": file_id(rel_str, i),
                "vector": vector,
                "payload": {
                    "source_file": rel_str,
                    "collection": collection,
                    "chunk_idx": i,
                    "total_chunks": len(chunks),
                    "text": chunk,
                    "embedded_at": datetime.utcnow().isoformat() + "Z",
                    "char_count": len(chunk)
                }
            })

        if collection not in collection_batches:
            collection_batches[collection] = []
        collection_batches[collection].extend(points)
        total_points += len(points)

        # Rate limit
        time.sleep(0.1)

    except Exception as e:
        errors.append((rel_str, str(e)))
        print(f"  ✗ Error: {rel_str}: {e}")

# Upsert all batches
if not DRY_RUN:
    print(f"\nUpserting {total_points} points across {len(collection_batches)} collections...")
    for collection, points in collection_batches.items():
        # Qdrant upsert in sub-batches of 100
        for i in range(0, len(points), 100):
            batch = points[i:i+100]
            try:
                result = upsert_points(collection, batch)
                print(f"  ✓ {collection}: {len(batch)} points upserted")
            except Exception as e:
                errors.append((collection, str(e)))
                print(f"  ✗ {collection}: {e}")

print(f"\n{'─'*50}")
print(f"{'[DRY RUN] ' if DRY_RUN else ''}Complete")
print(f"  Files processed : {len(all_files)}")
print(f"  Total chunks    : {total_chunks}")
print(f"  Points upserted : {total_points if not DRY_RUN else 'n/a (dry run)'}")
print(f"  Errors          : {len(errors)}")
if errors:
    for f, e in errors:
        print(f"    - {f}: {e}")
