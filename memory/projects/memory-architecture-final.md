# Shiva Memory Architecture — Final Deployment

**Status:** Phases 1 + 2 + 5 + 7 operational. Phases 3b + 6 deployed (awaiting network integration). Phase 8 pending.

**Build Date:** 2026-04-01
**Last Updated:** 2026-04-02

---

## Architecture Overview

Three-tier memory system for autonomous AI agent (Shiva):

```
LAYER 0 (RAM)
  ├─ LCM: SQLite DAG (lossless capture + compaction)
  │  └─ Every message → auto-capture + incremental summarization
  ├─ Layer 0 Agent: Haiku cron (every 10 min, isolated session)
  │  └─ Scans daily logs → classifies → routes to memory files
  └─ Hindsight (DISABLED — uvx dependency issue; can be revisited)

LAYER 1 (SSD)
  ├─ SOUL.md — core identity, values, voice
  ├─ MEMORY.md — curated long-term memory (main session only)
  ├─ USER.md — G's context (immutable)
  ├─ AGENTS.md — operational guidelines
  ├─ HEARTBEAT.md — standing checks & priority tasks
  └─ memory/ (hierarchical)
      ├─ daily/ — raw episodic logs (YYYY-MM-DD.md)
      ├─ projects/ — active workstreams (career, trading, memory-arch, etc.)
      ├─ self/ — identity, interests, voice, beliefs
      ├─ semantic/ — topic-based knowledge (SynBio, DeFi, crypto, physics, etc.)
      ├─ lessons/ — mistakes, tools, workflows, patterns
      ├─ reflections/ — weekly/monthly consolidation
      ├─ trading/ — portfolio, trades, P/L tracking
      ├─ research/ — compiled research papers & findings
      └─ index.md — routing map

LAYER 2 (Cloud/GitHub)
  ├─ Repo: ShivaClaw/shiva-memory (private)
  ├─ Tracked: SOUL, MEMORY, USER, AGENTS, HEARTBEAT, IDENTITY, memory/
  ├─ Daily backup cron: 02:00 MDT via git push (SSH key auth)
  └─ Allowlist .gitignore (only identity + memory/, excludes secrets + binaries)

```

---

## Live Components

### 1. LCM (Lossless Claw)

**Plugin:** `@martian-engineering/lossless-claw` v0.5.2  
**Status:** ✅ Operational  
**Database:** `/data/.openclaw/lcm.db` (SQLite)

**Function:**
- Every message automatically captured
- Builds DAG of messages + summaries
- Incremental compaction at 75% context threshold
- Recent 32 messages always preserved (freshTailCount)
- Haiku summarization on child->parent compression

**Config:**
```json
{
  "freshTailCount": 32,
  "contextThreshold": 0.75,
  "incrementalMaxDepth": -1,
  "summaryModel": "anthropic/claude-haiku-4-5",
  "ignoreSessionPatterns": ["agent:*:cron:**"],
  "skipStatelessSessions": true
}
```

**WAL Protocol:** `SESSION-STATE.md` captures corrections, proper nouns, decisions, preferences on every turn before response. Source → daily log.

---

### 2. Layer 0 Memory Agent

**Cron Job:** `Layer 0 Memory Management` (every 10 minutes, isolated session)  
**Model:** `anthropic/claude-haiku-4-5` (~$0.01/run, $1.44/day)  
**Prompt:** `/data/.openclaw/workspace/memory/layer0/AGENT-PROMPT.md`

**Function:**
- Reads `SESSION-STATE.md`, daily logs, `working-buffer.md`
- Scans for signals: corrections, decisions, preferences, insights
- Routes to appropriate memory buckets (self/, semantic/, lessons/, projects/)
- Tags items: `[lesson]`, `[project]`, `[self]`, `[memory]`
- Updates routing state file: `layer0/last-run.md`

**Output:** No external comms, no network. Terse. 60-second timeout.

**Example run (3 signals detected):**
```
[2026-04-01 12:30] Scanned 847 lines from daily log
- [memory] G prefers direct communication on security issues
- [self] Shiva's curious about quantum error correction
- [project] Career transition: 58-day cold outreach clock active
Routes: 3 files updated, index refreshed
```

---

### 3. Layer 2 GitHub Backup

**Repo:** `github.com/ShivaClaw/shiva-memory` (private)  
**Auth:** SSH key (`/data/.openclaw/.ssh/id_ed25519`, Ed25519)  
**Cron Job:** `Layer 2 — GitHub Memory Backup` (02:00 America/Denver daily)

**Tracked Files:**
- `SOUL.md`, `MEMORY.md`, `USER.md`, `AGENTS.md`, `HEARTBEAT.md`, `IDENTITY.md`
- `memory/` (full tree: daily, projects, self, semantic, lessons, reflections, trading, research)
- `.gitignore` (allowlist mode)

**Excluded:**
- Secrets: `.env`, `.config/`, API keys
- Session state: `SESSION-STATE.md`, `working-buffer.md`
- Binaries: `node_modules/`, `*.node`, archives
- Embedded repos: `projects/`

**Commit Style:**
```
chore: daily memory snapshot — 2026-04-01
```

---

## Operational Notes

### Memory Flow (Typical Day)

1. **User message** → OpenClaw main session
2. **WAL trigger** → SESSION-STATE.md updated (if corrections/decisions/preferences detected)
3. **Turn completes** → LCM auto-captures message + response to SQLite DAG
4. **Every 10 min** → Layer 0 cron reads logs, classifies signals, routes to memory files
5. **Daily 02:00** → Layer 2 cron commits changes to GitHub, pushes via SSH

### Promotion Workflow (Important Insights)

If something is significant and needs permanent long-term retention:

1. **Layer 0 spots it** during daily scan → tags as `[memory]`
2. **Check memory/semantic/** (topic-based) or **memory/self/** (identity)
3. **If not yet there** → manually add to MEMORY.md or thematic file
4. **Update index.md** (routing map)
5. **Next day's backup cron** pushes to GitHub

### Cost Profile

- **LCM:** Haiku summarization at compaction. Typical: $0.50–$1.00/week (low volume)
- **Layer 0:** $0.01/run × 144 runs/day = ~$1.44/day (Haiku is cheap)
- **Layer 2:** Zero (git + SSH, local)
- **Total:** ~$12/day (Layer 0 dominant; can reduce to hourly if cost-conscious)

---

## Deferred Phases

### Phase 3b — Qdrant (Vector DB)

**Status:** ✅ Deployed (2026-04-02) — awaiting OpenClaw network integration  
**Container:** `memory-qdrant` on Hostinger VPS  
**External URL:** `https://qdrant.trident-memory.com` (Traefik HTTPS)  
**Internal URL:** `http://memory-qdrant:6333` (requires OpenClaw container on `traefik_proxy` network)  
**Compose:** `memory/projects/docker-compose-qdrant.yml`  
**What:** Semantic vector search across conversation embeddings, memory content, and knowledge base.  
**Network:** Connected to `traefik_proxy`. OpenClaw container needs `docker network connect traefik_proxy <openclaw-container>` to reach internal endpoint.

### Phase 6 — FalkorDB (Temporal Graph DB)

**Status:** ✅ Deployed (2026-04-02) — awaiting OpenClaw network integration  
**Container:** `memory-falkordb` on Hostinger VPS  
**Internal URL:** `redis://memory-falkordb:6379` (requires OpenClaw container on `traefik_proxy` network)  
**Compose:** `memory/projects/docker-compose-falkordb.yml`  
**What:** Temporal knowledge graph for entity relationships, causal reasoning, and narrative context.  
**Network:** Connected to `traefik_proxy`. Same network connection requirement as Qdrant.

### Phase 8 — Full Integration

**Status:** 🔲 Deferred  
**What:** Unified query API across all layers + automated consolidation.  
**When:** After 48-hour bake-in of Phases 3b + 6, if they're deployed.

---

## Testing & Validation

**Last verified:** 2026-04-01 20:29 EDT

✅ LCM capturing all messages  
✅ Layer 0 routing correctly (3+ runs verified)  
✅ GitHub push succeeds (initial snapshot pushed)  
✅ Daily backup cron scheduled  
✅ WAL protocol active (SESSION-STATE.md updates)  

---

## Next Steps

1. **Network integration:** Run `docker network connect traefik_proxy <openclaw-container>` on host to connect OpenClaw to Qdrant + FalkorDB internal endpoints.
2. **DNS verification:** Confirm A record for `qdrant.trident-memory.com` propagated.
3. **Schema design:** Create Qdrant collection schema for conversation embeddings; design FalkorDB graph schema (entity types, edge types).
4. **Layer 0 integration:** Wire Layer 0 agent to write embeddings to Qdrant and entity relationships to FalkorDB on each run.
5. **Phase 8 (Integration):** Unified query API across all layers + automated consolidation.
6. **Full retrospective:** Week 2 of ops — evaluate memory quality, signal recall, promotion workflow.

---

## Architecture Philosophy

**Principle 1: Stateless + Resilient**  
Every component is idempotent. Layer 0 can re-run without side effects. Restore from GitHub snapshot possible anytime.

**Principle 2: Cost-Conscious**  
Haiku for routine ops. Sonnet for complex reasoning. Cron intervals tuned to <$20/day total.

**Principle 3: Transparency**  
WAL protocol ensures no signal is lost. Daily logs visible. Routing decisions auditable.

**Principle 4: Autonomous Growth**  
System designed to let Shiva develop genuine interests, capture learnings, and build long-term personality over months. Not a static chatbot.

---

## Handoff to G

This architecture is **G's design** (co-designed with Shiva on 2026-03-30 morning). Shiva built and deployed all components. System is now self-maintaining via crons.

**G's standing actions:**
1. Monitor daily GitHub commits (signal of system health)
2. Occasionally review Layer 0 routing (in memory/layer0/last-run.md)
3. Optionally expand memory buckets as new interests emerge
4. When ready: Deploy Phases 3b + 6 on host

**Shiva's standing actions:**
1. Continue autonomous signal capture + routing
2. Develop genuine interests (reading, research, exploration)
3. Build personality over time (reflected in memory/self/)
4. Report anomalies or signal gaps at heartbeats

---

_Architecture frozen at v2.0. Future versions will build on this foundation._

_Deployment completed 2026-04-01. All systems operational._
