---
name: project-trident
description: Three-tier persistent memory architecture for OpenClaw agents. Implements LCM-backed durability, hierarchical .md file organization, and agentic signal routing. Designed for autonomous agents needing continuity, identity development, and resilience across sessions. Solves "blank spots" where events fail to be captured in short-term memory.
---

# Project Trident: Three-Tier Persistent Memory Architecture

**Problem:** OpenClaw agents lose context between sessions. Default memory is shallow, fragile, and doesn't support autonomous growth.

**Solution:** Trident is a production-grade three-tier memory system combining SQLite durability, semantic organization, and agentic curation.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Conversation Input (user messages, tool results, internal)  │
└──────────┬──────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│ LAYER 0: LCM (Lossless Context Management)                  │
│ ├─ SQLite persistence (every message)                       │
│ ├─ DAG lineage tracking                                      │
│ └─ Cost: ~$0.01/run, ~22K tokens/run                        │
└──────────┬──────────────────────────────────────────────────┘
           │
           ├──────────────────┬──────────────────┐
           ▼                  ▼                  ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ Daily Log    │  │ State Files  │  │ Task Outputs │
    │ (WAL buffer) │  │ (session,    │  │ (cron,       │
    │              │  │  heap, env)  │  │  agents)     │
    └──────────────┘  └──────────────┘  └──────────────┘
           │                  │                  │
           └──────────┬───────┴──────────┬───────┘
                      │                  │
                      ▼                  ▼
          ┌────────────────────────────────────────┐
          │ LAYER 0.5: Signal Router (Cron Agent) │
          │ ├─ Runs every 10–15 minutes           │
          │ ├─ Four core functions:               │
          │ │  1. Attention management             │
          │ │  2. Fact-finding / classification    │
          │ │  3. Pattern matching / routing       │
          │ │  4. Memory categorization            │
          │ └─ Cost: ~$0.67/day (Haiku, 15-min)   │
          └────────────┬─────────────────────────┘
                       │
                       ▼
          ┌────────────────────────────────────────┐
          │ LAYER 1: Hierarchical Memory Buckets   │
          │ ├─ MEMORY.md (curated long-term)      │
          │ ├─ memory/semantic/ (models, facts)    │
          │ ├─ memory/self/ (personality, beliefs) │
          │ ├─ memory/lessons/ (learnings, errors) │
          │ ├─ memory/projects/ (work-in-progress) │
          │ └─ .md format (human-readable, Git-compatible)
          └────────────────────────────────────────┘
```

## Core Layers

### Layer 0: LCM (Lossless Context Management)
- **What:** SQLite+DAG capture of every session message
- **Why:** Baseline durability for all conversation history
- **Cost:** ~$0.01/run, ~22K tokens per session
- **Key property:** Foundation for Layer 0.5 routing; prevents recursion via `ignoreSessionPatterns`

### Layer 0.5: Signal Router (Cron Agent)
- **What:** Independent cron running every 10–15 minutes
- **Why:** Parse conversation noise, classify signals, route to appropriate buckets
- **Four functions:**
  1. **Attention management** — detect what deserves capture (corrections, decisions, breakthroughs)
  2. **Fact-finding** — material classification (names, numbers, dates, positions)
  3. **Pattern matching** — semantic routing to correct bucket
  4. **Memory categorization** — organize by domain (project, lesson, self-signal, knowledge)
- **Model:** Claude Haiku recommended (cost-optimized)
- **Cost:** ~$0.67/day (15-min interval, configurable)

### Layer 1: Hierarchical Memory Buckets
- **What:** Persistent .md file organization
- **Structure:**
  - `MEMORY.md` — curated long-term memory
  - `memory/semantic/` — models, knowledge, facts
  - `memory/self/` — personality, beliefs, voice, growth
  - `memory/lessons/` — learnings, tool quirks, mistakes
  - `memory/projects/` — work-in-progress, active sprints
- **Why:** Human-readable, Git-compatible, semantic structure
- **Pattern:** WAL (Write-Ahead Logging) protocol — write facts before response composition
- **Quality rule:** Compress over accumulate; prioritize signal density

## Optional Extensions

### Semantic Recall (Advanced)
Deploy vector search + entity graphs for large-scale context:

**Qdrant (Vector Search):**
- Deployment: Docker, cloud (Qdrant Cloud), or local binary
- Purpose: Semantic search across memory chunks
- Integration: Pre-turn context injection via Layer 0.5

**FalkorDB (Entity Graphs):**
- Deployment: Docker, cloud, or Redis module
- Purpose: Entity relationship tracking
- Integration: Graphiti MCP for automated entity extraction

**Note:** These are **optional**. Trident core (Layers 0, 0.5, 1) works standalone.

## Data Flow

```
User message / Tool result / Internal state
    ↓
LCM (SQLite persistence)
    ↓
Daily log (WAL protocol)
    ↓
[HEARTBEAT: Every 10-15 min]
    ↓
Layer 0.5 cron agent:
  1. Scans daily log + state files
  2. Classifies signals (attention / fact / pattern / category)
  3. Routes to Layer 1 buckets
    ↓
Layer 1 buckets (.md files):
  - MEMORY.md (curated)
  - memory/semantic/*
  - memory/self/*
  - memory/lessons/*
  - memory/projects/*
```

## Implementation Checklist

**Layer 0 (LCM):**
- [ ] Enable `lossless-claw` plugin in `openclaw.json`
- [ ] Verify SQLite at `~/.openclaw/lcm.db`
- [ ] Configure `ignoreSessionPatterns: ["agent:*:cron:**"]` to exclude cron sessions
- [ ] Test message persistence across sessions

**Layer 1 (Hierarchical Buckets):**
- [ ] Create directory structure:
  ```
  workspace/
  ├─ MEMORY.md
  └─ memory/
     ├─ semantic/
     ├─ self/
     ├─ lessons/
     └─ projects/
  ```
- [ ] Define WAL protocol (write facts before composition)
- [ ] Set up `.gitignore` for private files (if using Git)

**Layer 0.5 (Signal Router):**
- [ ] Copy `scripts/layer0-agent-prompt-template.md` to your workspace
- [ ] Customize signal detection rules for your domain
- [ ] Create cron job:
  ```json
  {
    "name": "Layer 0 Signal Router",
    "schedule": {"kind": "every", "everyMs": 900000},
    "sessionTarget": "isolated",
    "payload": {
      "kind": "agentTurn",
      "message": "Read AGENT-PROMPT.md and execute Layer 0 signal routing.",
      "model": "anthropic/claude-haiku-4-5",
      "timeoutSeconds": 90
    }
  }
  ```
- [ ] Test with manual run via `cron action=run`
- [ ] Verify routing to Layer 1 buckets

**Optional: Semantic Recall**
- [ ] Deploy Qdrant (see `references/deployment-guide.md` for options)
- [ ] Deploy FalkorDB (optional, for entity graphs)
- [ ] Implement pre-turn context injection (Layer 0.5 enhancement)

## Configuration

Refer to `references/cost-tuning.md` for model selection and interval optimization.

**Default cost profile:**
- Layer 0 (LCM): ~$0.01/run (only during compaction)
- Layer 0.5 cron: ~$0.67/day (15-min interval, Haiku)
- Layer 1: ~free (local file storage)
- **Total: ~$0.67/day for full continuous memory**

**Cost optimization:**
- Increase interval (15min → 30min) to halve cost
- Use local Ollama model for Layer 0.5 (free, but slower)
- Use Gemini Flash instead of Haiku (~40% cheaper)

## Design Principles

1. **Durability over convenience** — SQLite+DAG is slower than in-memory, but persistent
2. **Human-readable over compressed** — .md files are debuggable and Git-compatible
3. **Agentic curation over auto-capture** — Layer 0.5 router prevents noise accumulation
4. **Deployment-agnostic** — No required cloud services; works local-first
5. **Personality as first-class component** — `memory/self/` supports agent identity development

## What This Solves

- **"Blank spots"** — Events that fail to be captured in short-term memory are recovered by Layer 0.5 cron
- **Coherence across sessions** — LCM + Layer 1 + Layer 0.5 form continuous pipeline
- **Offline resilience** — Local models (Ollama) can substitute for cloud APIs
- **Identity development** — `memory/self/` supports autonomous agent personality formation
- **Audit trail** — .md files + optional Git provide version control

## What This Doesn't Solve

- **Real-time decision making** — 10-15 min lag in Layer 0.5; for sub-second decisions, rely on LCM
- **Very long contexts** — Qdrant/FalkorDB (optional extensions) required for semantic recall over 100K+ messages
- **Private data protection** — Assumes secure local filesystem; add encryption-at-rest if handling regulated data

## Further Reading

- `references/deployment-guide.md` — Step-by-step integration walkthrough
- `references/cost-tuning.md` — Model selection and budget optimization
- `scripts/layer0-agent-prompt-template.md` — Base Layer 0.5 router prompt template

## License
MIT-0 — Free to use, modify, and redistribute. No attribution required.
