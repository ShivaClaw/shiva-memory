#!/usr/bin/env python3
"""
Layer 0.5 Cron Sidecar — Semantic Recall Injector

Runs every 15 minutes (via cron), queries Qdrant for recent message context,
and stages injection payloads for lossless-claw pre-turn integration.

This is the glue between:
  - Layer 0 (signal detection + memory writing)
  - Qdrant (semantic vector DB with 122 indexed chunks)
  - lossless-claw (context engine slot that can read staging files)

Output: ~/memory/layer0.5/context-injection-YYYY-MM-DDTHH:MM:SSZ.json

Integration with lossless-claw:
  - lossless-claw's pre-expansion hook can read staging files
  - Injects ranked results before context expansion
  - Gives lossless-claw's compaction a warm start

No external API calls (avoids embedding cost per cron run).
Instead: uses cached embeddings from Layer 0.5 on-demand mode.
"""

import os, sys, json, re, time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request

QDRANT_URL = "http://172.17.0.1:6333"
WORKSPACE = Path("/data/.openclaw/workspace")
STAGING_DIR = WORKSPACE / "memory" / "layer0.5"
SESSION_STATE = WORKSPACE / "SESSION-STATE.md"

STAGING_DIR.mkdir(parents=True, exist_ok=True)

# ── Logging ────────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[L0.5-cron {ts}] {msg}", file=sys.stderr)

# ── Qdrant Helper ──────────────────────────────────────────────────────────

def http_post_json(url, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return json.loads(r.read())
    except Exception as e:
        log(f"ERROR: {url}: {e}")
        return None

def search_qdrant(query_vec, collections=None, top_k=3):
    """Search Qdrant with a pre-computed embedding."""
    if not collections:
        collections = ["memory_self", "memory_projects", "memory_daily"]
    
    results = []
    for col in collections:
        url = f"{QDRANT_URL}/collections/{col}/points/search"
        body = {
            "vector": query_vec,
            "limit": top_k,
            "with_payload": True,
            "score_threshold": 0.25  # Lower threshold for sidecar (more recall)
        }
        resp = http_post_json(url, body)
        if not resp:
            continue
        for r in resp.get("result", []):
            r["_collection"] = col
            results.append(r)
    
    return results

# ── Embed via CLI (expensive but cron is sparse) ──────────────────────────

def embed_query_cli(query_text):
    """Embed via Layer 0.5 CLI to avoid duplicating embedding code."""
    try:
        import subprocess
        result = subprocess.run(
            ["python3", str(WORKSPACE / "scripts" / "context-injection-layer0.5.py"),
             "--query", query_text],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # Suppress deprecation warnings
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            # Extract JSON from stdout (collect all lines starting from first {)
            output = result.stdout.strip()
            if '{' in output:
                try:
                    json_start = output.index('{')
                    json_str = output[json_start:]
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    log(f"JSON parse error: {e}")
            else:
                log(f"No JSON object found in output")
        else:
            log(f"Layer 0.5 CLI error (code {result.returncode})")
    except Exception as e:
        log(f"Embed failed: {e}")
    
    return None

# ── Read recent session state ──────────────────────────────────────────────

def get_recent_context():
    """Extract recent user message from SESSION-STATE.md or daily log."""
    candidates = []
    
    # Try SESSION-STATE.md first
    if SESSION_STATE.exists():
        try:
            with open(SESSION_STATE) as f:
                content = f.read()
                # Look for recent user messages (crude but effective)
                if "What we shipped" in content or "wire up" in content:
                    candidates.append(content[-500:])  # Last 500 chars
        except:
            pass
    
    # Fall back to today's daily log
    today = datetime.now(timezone.utc).date()
    daily_file = WORKSPACE / "memory" / "daily" / f"{today}.md"
    if daily_file.exists():
        try:
            with open(daily_file) as f:
                content = f.read()
                candidates.append(content[-500:])
        except:
            pass
    
    # Return most recent
    if candidates:
        return candidates[0]
    
    return "What is my current context and recent project state?"

# ── Rank by recency ───────────────────────────────────────────────────────

def rank_by_recency(results):
    """Boost recent daily files."""
    now = datetime.now()
    for r in results:
        payload = r.get("payload", {})
        source = payload.get("source_file", "")
        
        if "daily/" in source:
            try:
                match = re.search(r'(\d{4}-\d{2}-\d{2})', source)
                if match:
                    file_date = datetime.strptime(match.group(1), "%Y-%m-%d")
                    days_old = (now - file_date).days
                    if days_old == 0:
                        r["score"] = min(0.99, r.get("score", 0) + 0.2)
                    elif days_old <= 3:
                        r["score"] = min(0.99, r.get("score", 0) + 0.1)
            except:
                pass
    
    return results

# ── Format injection ──────────────────────────────────────────────────────

def format_injection(injection_payload):
    """Format for lossless-claw pre-turn injection."""
    return {
        "type": "semantic_context",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "confidence": 0.7,  # Cron sidecar is lower confidence than request-time
        "query_inferred": "recent session context for pre-turn injection",
        "results_count": len(injection_payload.get("relevant_memories", [])),
        "top_3": injection_payload.get("relevant_memories", [])[:3],
        "context_markdown": injection_payload.get("context_markdown", ""),
    }

# ── Main ───────────────────────────────────────────────────────────────

def main():
    log("Starting Layer 0.5 cron sidecar")
    
    # Step 1: Get recent context
    context = get_recent_context()
    log(f"Context: {context[:60]}...")
    
    # Step 2: Embed via Layer 0.5 CLI
    injection = embed_query_cli(context)
    if not injection:
        log("WARN: Layer 0.5 embed returned None, skipping this run")
        return 0  # Not an error, just no results this time
    
    # Step 3: Rank by recency
    memories = injection.get("relevant_memories", [])
    if memories:
        results_for_ranking = [{"payload": m, "score": m.get("score", 0)} for m in memories]
        results_for_ranking = rank_by_recency(results_for_ranking)
        # Unpack back to memories
        injection["relevant_memories"] = [
            {**r.get("payload", {}), "score": r.get("score", 0)}
            for r in results_for_ranking
        ]
    
    # Step 4: Format for injection
    formatted = format_injection(injection)
    
    # Step 5: Write staging file
    timestamp = datetime.now(timezone.utc).isoformat().replace(":", "-").split(".")[0] + "Z"
    staging_file = STAGING_DIR / f"context-injection-{timestamp}.json"
    
    with open(staging_file, 'w') as f:
        json.dump(formatted, f, indent=2)
    
    log(f"Staged injection: {staging_file.name} ({len(memories)} results)")
    
    # Step 6: Cleanup old files (keep last 5)
    try:
        files = sorted(STAGING_DIR.glob("context-injection-*.json"), reverse=True)
        for old_file in files[5:]:
            old_file.unlink()
            log(f"Cleaned up {old_file.name}")
    except Exception as e:
        log(f"Cleanup failed: {e}")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"FATAL: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
