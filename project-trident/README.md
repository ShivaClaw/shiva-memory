# Project Trident: Best-in-Class Persistent Memory for AI Agents

**A three-tier architecture that solves the AI agent memory problem once and for all.**

---

## What Is Project Trident?

Project Trident is a production-grade persistent memory system for OpenClaw AI agents. It addresses the fundamental challenge of AI agent continuity: **how do you give an agent a memory that survives restarts, grows intelligently, and never loses critical context?**

Most agent frameworks treat memory as an afterthought—dumping everything into flat files or hoping vector databases magically fix context loss. Project Trident takes a different approach: **hierarchical storage with intelligent routing**, modeled after how computer systems manage memory (RAM → SSD → HDD).

The result is an agent that:
- **Never forgets important events** (even across sessions)
- **Develops genuine personality and identity** over time
- **Maintains operational continuity** through crashes, compactions, and code updates
- **Stays cost-efficient** (sub-$1/day for 24/7 operation)
- **Works deployment-agnostic** (local-first, cloud optional)

---

## What Does It Do?

### Core Capabilities

1. **Lossless Context Management (LCM)**  
   Every message, tool call, and system event is captured in SQLite with a DAG structure. Nothing is ever truly lost—even after aggressive compaction.

2. **Signal-Based Memory Routing**  
   A lightweight agent (Layer 0.5) runs every 15–30 minutes, scanning recent activity for memory-worthy signals:
   - Corrections ("It's X, not Y")
   - Project updates
   - Self-awareness moments
   - User preferences
   - Mistakes and learnings
   
   These signals are classified and routed to semantic buckets (MEMORY.md, self/, lessons/, projects/).

3. **Hierarchical Storage**  
   - **Layer 0 (Foundation):** LCM SQLite database + DAG lineage
   - **Layer 0.5 (Router):** Cron-based signal classifier + memory routing agent
   - **Layer 1 (Durable Storage):** Curated .md files organized by topic (fast human/agent reads)

4. **Personality Development**  
   Identity isn't an add-on—it's a first-class architectural component. Files like `self/beliefs.md`, `self/patterns.md`, and `self/growth-log.md` track how the agent evolves over weeks and months.

5. **Cost-Optimized**  
   Layer 0.5 runs on Claude Haiku (~$0.67/day). LCM compaction uses cheap models. Total infrastructure cost: **under $1/day** for full 24/7 memory persistence.

---

## How Is It Engineered?

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 0.5: Signal Router (Haiku, 15-30min cron)            │
│  ├─ Scans daily logs via write-ahead logging protocol       │
│  ├─ Classifies signals (correction, project, self, memory)  │
│  └─ Routes to Layer 1 buckets                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Hierarchical .md Storage                          │
│  ├─ MEMORY.md (long-term curated memory)                    │
│  ├─ memory/daily/YYYY-MM-DD.md (raw episodic logs)          │
│  ├─ memory/self/ (identity, beliefs, patterns, growth)      │
│  ├─ memory/lessons/ (mistakes, tool quirks, workflows)      │
│  ├─ memory/projects/ (active workstreams)                   │
│  └─ memory/reflections/ (weekly/monthly consolidation)      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 0: LCM (Lossless Context Management)                 │
│  ├─ SQLite database (DAG structure, parent/child refs)      │
│  ├─ Every message + tool call preserved                     │
│  ├─ Compaction summaries link back to source messages       │
│  └─ lcm_grep, lcm_expand, lcm_expand_query for deep recall  │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

**1. Write-Ahead Logging (WAL Protocol)**  
Never rely on chat history as persistent storage. Every important event is immediately written to `SESSION-STATE.md` or the daily log *before* composing a response. This prevents "blank spots" where critical context gets lost between heartbeats.

**2. Quality Over Accumulation**  
Layer 0.5 is instructed to **compress, not append**. One clean, dense entry beats five redundant notes. Signal detection prioritizes corrections (highest priority), project state changes, and self-awareness moments.

**3. Deployment-Agnostic Design**  
No required cloud services. No mandatory Docker. No vendor lock-in. Trident works:
- Local-only (files + SQLite)
- With optional Git backup (any Git provider)
- With optional vector search (Qdrant: Docker, cloud, or binary)
- With optional entity graphs (FalkorDB: Docker, cloud, or Redis module)

**4. Personality as Infrastructure**  
`memory/self/` isn't metadata—it's core architecture. Agents develop:
- **Beliefs** (worldview, ethical principles)
- **Interests** (topics they find fascinating)
- **Patterns** (recurring behaviors, communication style)
- **Growth log** (weekly reflections on identity development)

**5. Separation of Concerns**  
- **Layer 0 (LCM):** Raw persistence, no curation
- **Layer 0.5 (Signal Router):** Classification + routing
- **Layer 1 (Buckets):** Curated semantic storage

Each layer has a single job. No monoliths.

---

## Why Is It Best-in-Class?

| Feature | Project Trident | Mem0 | LangChain Memory | AutoGPT Forge | Semantic Kernel |
|---------|----------------|------|------------------|---------------|-----------------|
| **Lossless capture** | ✅ (LCM SQLite+DAG) | ❌ | ❌ | ❌ | ❌ |
| **Signal routing** | ✅ (Layer 0.5 cron) | ❌ | ❌ | ❌ | ❌ |
| **Personality development** | ✅ (`memory/self/`) | ❌ | ❌ | ❌ | ❌ |
| **Human-readable storage** | ✅ (.md files) | ❌ (vectors only) | ⚠️ (JSON) | ⚠️ (JSON) | ❌ |
| **Deployment-agnostic** | ✅ | ❌ (cloud-only) | ✅ | ✅ | ✅ |
| **Cost-optimized** | ✅ (<$1/day) | ⚠️ (API-dependent) | ⚠️ | ⚠️ | ⚠️ |
| **Git-compatible** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Identity continuity** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Deep recall (lcm_expand_query)** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Offline resilience** | ✅ (local models) | ❌ | ⚠️ | ⚠️ | ⚠️ |

**Why the difference?**

Most memory systems focus on *search* (vector DBs, embeddings). Trident focuses on **curation**. Layer 0.5 acts like a personal librarian, classifying signals and routing them to the right semantic buckets. The result is a memory that's not just searchable, but *organized* and *meaningful*.

---

## What's the Workflow?

### Day 1: Setup (30 minutes)

1. Enable `lossless-claw` plugin in `openclaw.json`
2. Create directory structure:
   ```
   workspace/
   ├─ MEMORY.md
   └─ memory/
      ├─ daily/
      ├─ semantic/
      ├─ self/
      ├─ lessons/
      └─ projects/
   ```
3. Copy `scripts/layer0-agent-prompt-template.md` to your workspace
4. Customize signal detection rules for your domain
5. Create Layer 0.5 cron job (15-min interval, Haiku model)
6. Test with manual run

### Day 2–7: Observation

- Let Layer 0.5 run autonomously
- Check `memory/daily/*.md` logs
- Verify signals are being routed correctly
- Tune classification rules if needed

### Week 2+: Continuous Operation

- Layer 0.5 runs 24/7, classifying signals
- `MEMORY.md` grows intelligently (not linearly)
- `memory/self/` tracks personality development
- Optional: Add Git backup cron
- Optional: Deploy Qdrant for semantic search

---

## Optional Extensions

### Semantic Recall (Advanced)

For agents handling 100K+ messages, add vector search + entity graphs:

**Qdrant (Vector Search):**
- **Deployment options:** Docker, Qdrant Cloud, or local binary
- **Purpose:** Semantic search across memory chunks
- **Integration:** Pre-turn context injection via Layer 0.5

**FalkorDB (Entity Graphs):**
- **Deployment options:** Docker, cloud, or Redis module
- **Purpose:** Entity relationship tracking
- **Integration:** Graphiti MCP for automated entity extraction

**Note:** These are **optional**. Trident core (Layers 0, 0.5, 1) works standalone.

---

## Who Is This For?

- **AI researchers** building long-running autonomous agents
- **Power users** who want continuity across OpenClaw sessions
- **Developers** prototyping agentic systems with real memory
- **Anyone** frustrated with "the agent forgot X" problems

---

## What's Included?

- `SKILL.md` — Core architecture guide
- `references/deployment-guide.md` — Step-by-step setup
- `references/cost-tuning.md` — Model selection and budget optimization
- `scripts/layer0-agent-prompt-template.md` — Customizable signal router prompt

---

## Getting Started

1. **Install the skill:**
   ```bash
   clawhub install shivaclaw/project-trident
   ```

2. **Read the deployment guide:**
   ```bash
   cat ~/.openclaw/skills/project-trident/references/deployment-guide.md
   ```

3. **Follow the checklist** in `SKILL.md`

4. **Test Layer 0.5** with a manual cron run

5. **Let it run** for a week and observe

---

## License

MIT-0 — Free to use, modify, and redistribute. No attribution required.

---

## Questions?

- **GitHub:** [ShivaClaw/shiva-memory](https://github.com/ShivaClaw/shiva-memory)
- **ClawHub:** [shivaclaw/project-trident](https://clawhub.ai/shivaclaw/project-trident)
- **Discord:** [#project-trident](https://discord.com/invite/clawd)

---

**Like a lobster shell, memory has layers. Make them durable.**
