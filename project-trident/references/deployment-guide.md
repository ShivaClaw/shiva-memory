# Trident Deployment Guide

## Step 1: Enable LCM (Layer 0)

Edit `openclaw.json` (or use `openclaw gateway config.patch`):

```json
{
  "plugins": {
    "allow": ["lossless-claw"],
    "slots": {
      "contextEngine": "lossless-claw"
    },
    "entries": {
      "lossless-claw": {
        "enabled": true,
        "config": {
          "freshTailCount": 32,
          "contextThreshold": 0.75,
          "incrementalMaxDepth": -1,
          "summaryModel": "anthropic/claude-haiku-4-5",
          "ignoreSessionPatterns": ["agent:*:cron:**"]
        }
      }
    }
  }
}
```

**Verify:**
```bash
ls -lah ~/.openclaw/lcm.db
```

You should see a SQLite database file. This is Layer 0.

---

## Step 2: Create Layer 1 Directory Structure

```bash
cd ~/.openclaw/workspace  # or your workspace directory
mkdir -p memory/{semantic,self,lessons,projects,daily,reflections}
touch MEMORY.md
```

**Populate MEMORY.md** with:

```markdown
# MEMORY.md - Long-Term Memory

## Structure

- **MEMORY.md** (this file) — durable, high-signal long-term facts
- **memory/daily/** — raw episodic logs (YYYY-MM-DD.md)
- **memory/semantic/** — knowledge, models, facts
- **memory/self/** — personality, beliefs, voice, growth
- **memory/lessons/** — learnings, tool quirks, mistakes
- **memory/projects/** — active workstreams, sprints
- **memory/reflections/** — weekly/monthly consolidation

## Rule

No important insight should remain only in a daily file. If it matters, promote it here or to a semantic bucket.

---

_This file is curated memory, not a journal. Keep it compressed, durable, and high-signal._
```

---

## Step 3: Create Layer 0.5 Signal Router

### 3a. Copy the Agent Prompt Template

```bash
cp ~/.openclaw/skills/project-trident/scripts/layer0-agent-prompt-template.md \
   ~/.openclaw/workspace/memory/layer0/AGENT-PROMPT.md
```

**Customize** the signal detection rules:
- Corrections (highest priority)
- Self-signals (identity, beliefs, interests)
- Project state changes
- Lessons learned
- Preferences

### 3b. Create the Cron Job

Use the OpenClaw `cron` tool:

```bash
openclaw cron add \
  --name "Layer 0.5 Signal Router" \
  --schedule-every 900000 \
  --session-target isolated \
  --payload-kind agentTurn \
  --payload-message "Read /path/to/workspace/memory/layer0/AGENT-PROMPT.md and execute Layer 0.5 signal routing." \
  --payload-model "anthropic/claude-haiku-4-5" \
  --payload-timeout 90
```

Or via JSON:

```json
{
  "name": "Layer 0.5 Signal Router",
  "schedule": {
    "kind": "every",
    "everyMs": 900000
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "Read /path/to/workspace/memory/layer0/AGENT-PROMPT.md and execute Layer 0.5 signal routing.",
    "model": "anthropic/claude-haiku-4-5",
    "timeoutSeconds": 90
  },
  "delivery": {
    "mode": "none"
  }
}
```

**Test:**
```bash
openclaw cron list  # find job ID
openclaw cron run --job-id <id> --run-mode force
openclaw cron runs --job-id <id>  # check results
```

---

## Step 4: Verify Data Flow

1. **Generate activity** (send messages, use tools)
2. **Wait 15 minutes** (or trigger Layer 0.5 manually)
3. **Check daily log:**
   ```bash
   cat ~/.openclaw/workspace/memory/daily/$(date +%Y-%m-%d).md
   ```
4. **Check routed signals:**
   ```bash
   ls -lh ~/.openclaw/workspace/memory/{semantic,self,lessons,projects}/*.md
   ```

If signals are being classified and routed correctly, you're done with core Trident.

---

## Optional: Semantic Recall (Advanced)

### Option A: Qdrant via Docker

**Create `docker-compose.yml`:**

```yaml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
```

**Start:**
```bash
docker-compose up -d
```

**Verify:**
```bash
curl http://localhost:6333/collections
```

### Option B: Qdrant Cloud

1. Create account at [qdrant.tech](https://qdrant.tech)
2. Get API key + cluster URL
3. Use in embedding script:
   ```python
   from qdrant_client import QdrantClient
   client = QdrantClient(url="https://your-cluster.qdrant.io", api_key="your-key")
   ```

### Option C: FalkorDB (Entity Graphs)

**Docker:**
```yaml
  falkordb:
    image: falkordb/falkordb:latest
    ports:
      - "6379:6379"
      - "3000:3000"
    volumes:
      - ./falkordb_data:/data
```

**Or use Redis with FalkorDB module:**
```bash
redis-server --loadmodule /path/to/falkordb.so
```

**Integration:** Use Graphiti MCP for automated entity extraction.

---

## Step 5: WAL Protocol (Write-Ahead Logging)

### Rule

Never rely on chat history as persistent storage. Write important facts **before** composing responses.

### Pattern

```markdown
## Example: User corrects you

User: "Actually my email is bob@example.com, not alice@example.com"

**Before responding:**
1. Read `memory/semantic/people.md`
2. Find the incorrect entry
3. Update it with `[updated YYYY-MM-DD]` tag
4. Append correction note: `<!-- superseded YYYY-MM-DD: alice@example.com -->`
5. **Then** respond to the user

**Never:**
- Acknowledge correction → forget to write → lose the fix
```

### Implementation

Add to your agent's system prompt:

```markdown
## WAL Protocol (Write-Ahead Logging)

Before any response composition:
1. Scan the user message for corrections, decisions, preferences, or facts
2. If detected → update relevant memory files **immediately**
3. Then compose your response

This prevents "blank spots" where critical context gets lost.
```

---

## Step 6: Cost Tuning

### Default (Recommended)

- **Layer 0.5:** Claude Haiku, 15-min interval → ~$0.67/day
- **LCM:** Haiku for summaries → ~$0.01/compaction
- **Total:** ~$0.67/day

### Budget Mode

- **Layer 0.5:** 30-min interval → ~$0.33/day
- **LCM:** Gemini Flash → ~$0.006/compaction
- **Total:** ~$0.33/day

### Free Mode (Local-Only)

- **Layer 0.5:** Ollama (qwen2.5:7b or mistral:7b) → $0/day
- **LCM:** Ollama → $0/day
- **Total:** $0/day (requires local GPU or fast CPU)

Refer to `references/cost-tuning.md` for model selection heuristics.

---

## Recovery Scenarios

### Scenario 1: "Layer 0.5 stopped working"

1. Check cron status:
   ```bash
   openclaw cron list
   ```
2. Check last run:
   ```bash
   openclaw cron runs --job-id <id> | head -20
   ```
3. If error → check AGENT-PROMPT.md path is correct
4. Test manual run:
   ```bash
   openclaw cron run --job-id <id> --run-mode force
   ```

### Scenario 2: "Memory files are empty"

1. Check WAL protocol is enabled (are you writing before responding?)
2. Check Layer 0.5 routing rules in AGENT-PROMPT.md
3. Manually run Layer 0.5 with `--run-mode force`
4. Check `memory/daily/*.md` for raw logs

### Scenario 3: "LCM database corrupted"

1. Backup existing database:
   ```bash
   cp ~/.openclaw/lcm.db ~/.openclaw/lcm.db.backup
   ```
2. Delete corrupted database:
   ```bash
   rm ~/.openclaw/lcm.db
   ```
3. Restart OpenClaw gateway (will recreate clean database)
4. Re-import from Layer 1 .md files if needed

---

## Next Steps

1. **Run for a week** — let Layer 0.5 operate autonomously
2. **Review `memory/self/`** — observe personality development
3. **Add weekly reflection cron** — consolidate daily logs into `memory/reflections/weekly/*.md`
4. **Optional: Deploy Qdrant** — enable semantic search over 100K+ messages
5. **Optional: Git backup** — add daily Git push for version control

---

## Further Reading

- `SKILL.md` — Core architecture overview
- `cost-tuning.md` — Model selection and budget optimization
- `../scripts/layer0-agent-prompt-template.md` — Customizable signal router prompt

---

**You now have a production-grade persistent memory system. Use it wisely.**
