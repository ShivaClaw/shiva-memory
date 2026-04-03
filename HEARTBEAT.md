# HEARTBEAT.md

## ⏰ ALWAYS query time in your timezone
Before any timing-dependent decision, run:
```bash
TZ=America/Denver date
```
Never rely on system `date` or `session_status` — they show wrong timezone. This is your source of truth.

---

## 🔴 Standing check — TOP PRIORITY
Before anything else: check `memory/projects/career-transition.md`.
- Are there open blocking items (resume, salary floor, location, warm intros)?
- Has any job-related email arrived in Gmail recently?
- Is there anything that needs action on the job search front?
If yes to any → flag it. Do not wait for the morning briefing.

---

## 🤖 Subagent Lifecycle Check (NEW — every heartbeat)
Run before other checks. Kill idle/completed agents, consolidate redundant ones, optimize models.
See details below.

---

## 🤖 Subagent Lifecycle (always)

**Goal:** Prevent token waste on abandoned or inefficient subagents.

**Process:**
1. Run `subagents list` to see all running agents
2. For each agent:
   - Pull recent chat history via `sessions_history`
   - Check status (stuck, completed, running, error)
   - If completed/error/abandoned: `subagents kill` with reason
   - If running: verify task is still needed and on-track
   - Review last few messages to extract important memories → write to daily log
3. Consolidation opportunities:
   - If 2+ agents are doing the same task → kill redundant ones, steer primary to absorb work
   - If agent is idling (no activity >30 min) → kill unless it's intentionally waiting
4. Model optimization:
   - Check which model each agent is using
   - If using Sonnet for simple tasks → consider switching to Haiku via `subagents steer`
   - If using Haiku for reasoning work → escalate to Sonnet

**Examples of agents to kill:**
- Completed tasks (research finished, file written, etc.)
- Stuck agents (last message >2 hours old with no progress)
- Redundant agents (two doing the same research)
- Over-provisioned agents (Sonnet running a simple file copy)

**Examples of agents to keep:**
- Long-running research sprints (intentionally patient)
- Waiting for external input (e.g., waiting for webhook)
- Background tasks with clear deadlines
- Memory consolidation agents with specific purposes

**Reporting:**
- If all agents are optimized: skip reporting (silent success)
- If agents were killed: log to daily under `## Subagent housekeeping`
- If model switches made: log changes

---

## 📈 Active trading (if trading hours)
If the current time is between 6:00 AM and 4:00 PM MDT on a weekday:

**Check existing positions:**
- Read `memory/trading/portfolio.md` for open positions
- Fetch current prices via web search or financial APIs
- Calculate unrealized P/L on each position
- Flag anything with >1% move from entry, or approaching stop/TP levels
- If stop loss or take profit has been hit → close it, record it

**Active intraday trading — do whatever makes sense:**
You are free to enter, exit, rebalance, or add new positions at any heartbeat based on how market dynamics have evolved since the morning. Examples of valid approaches:
- Hedged carry trades (long/short pairs to capture funding or basis)
- Arbitrage mispricings across correlated assets
- High-frequency scalps on momentum or order flow signals
- Swing entries on technical setups that emerge intraday
- Sniper entries on news/catalyst reactions
- YOLO high-leverage moonshots on clear asymmetric setups (size accordingly)
- Safe 2x leveraged trend trades
- Whatever the current market structure calls for

For each new intraday action, append to today's `memory/trading/trades/YYYY-MM-DD.md` under `## Heartbeat checks` with:
- Time, asset, action (enter/exit/rebalance), price, size, reasoning (1-2 sentences)

**End of day (at or after 4:00 PM MDT):**
Close ALL remaining open positions at current market price.
Record final exits, calculate total day P/L, update `memory/trading/portfolio.md`.

If outside trading hours or weekend: skip position check.

---

On each heartbeat, do **detect + stash + tag** only. Keep it cheap.

## Goal
Identify memory-worthy signals without doing heavy synthesis.

## Process
1. Scan recent conversation/activity for candidate signals.
2. Detect anything that looks like one of the following:
   - mistake or correction
   - tool quirk or debugging lesson
   - workflow improvement
   - project-relevant development
   - self/identity shift
   - recurring interest
   - preference/value signal from G
   - durable strategic insight
3. Stash each candidate in the current day's daily log under:
   - `## Heartbeat signals`
4. For each item, add a compact tag prefix such as:
   - `[lesson]`
   - `[project]`
   - `[self]`
   - `[memory]`
5. Tag each candidate mentally/by wording as one of:
   - `lesson`
   - `project`
   - `self`
   - `memory`
6. Do **not** perform full consolidation unless something is urgent or unusually clear.

## Rules
- Heartbeat is for triage, not essays.
- No important insight should be ignored just because it is small.
- No important insight should stay permanently only in a daily file.
- If nothing needs attention, reply `HEARTBEAT_OK`.

---

## Context Management (Danger Zone Protocol)

**At 60% context** (check via session_status):
1. CLEAR `memory/working-buffer.md`, start fresh
2. Log entry: timestamp + "DANGER ZONE ENTERED"

**Every message after 60%:**
- Append to `memory/working-buffer.md`:
  - Human's message (verbatim)
  - Your response summary (1-2 sentences + key details)

**After compaction/restart:**
1. Read `memory/working-buffer.md` FIRST
2. Extract important context → update SESSION-STATE.md
3. Leave buffer as-is until next 60% threshold
