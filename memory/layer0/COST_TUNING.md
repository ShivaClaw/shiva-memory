# Layer 0 — Cost Tuning Guide

**Budget:** $1.00/day (fixed ceiling)

Layer 0 runs on a recurring cron. Cost = (runs per day) × (cost per run). We can tune either variable.

---

## Current Config (2026-04-02)

- **Model:** `anthropic/claude-haiku-4-5`
- **Interval:** 15 minutes (900,000ms)
- **Runs/day:** 96
- **Cost/run:** ~$0.007
- **Total/day:** ~$0.67 ✅

---

## Model Options (Sorted by Cost)

| Model | Cost/Run | Interval for $1/day | Runs/Day | Notes |
|-------|----------|---------------------|----------|-------|
| `openrouter/google/gemini-2.5-flash` | $0.002 | 2.9 min | 500 | Fastest, cheapest. Can run more frequently. |
| `anthropic/claude-haiku-4-5` | $0.007 | 10 min | 144 | Current. Balanced. Reliable. |
| `openrouter/google/gemini-2.0-flash-exp` | $0.002 | 2.9 min | 500 | Experimental Flash variant. |
| `openai/gpt-4.1` | $0.05 | 72 min | 20 | High-quality reasoning but slow interval. |
| `anthropic/claude-sonnet-4-5` | $0.08 | 115 min | 12.5 | Too expensive for frequent runs. |

**Note:** Cost estimates assume ~2K input tokens, ~500 output tokens per run (typical Layer 0 workload).

---

## Tuning Strategy

**To increase run frequency (stay under $1/day):**
- Switch to Gemini 2.5 Flash → can run every 2.9 minutes instead of 10

**To use higher-quality model (stay under $1/day):**
- Switch to GPT-4.1 → interval increases to 72 minutes (1.2 hours)

**To stay at current 10-min interval:**
- Haiku is optimal (already there)

---

## How to Change

### Change Model (Keep 10-min interval):
```bash
cron update --job-id 83825ad4-06ec-4fbf-a230-b4ece3d5274e \
  --patch '{"payload": {"model": "openrouter/google/gemini-2.5-flash"}}'
```

### Change Interval (Keep Haiku):
```bash
cron update --job-id 83825ad4-06ec-4fbf-a230-b4ece3d5274e \
  --patch '{"schedule": {"kind": "every", "everyMs": 300000}}'  # 5 min
```

### Change Both:
Update via `cron update` with both `payload.model` and `schedule.everyMs` in the patch.

---

## Monitoring

Check daily cost:
```bash
# Count runs in last 24h
grep "L0 \[" memory/daily/$(date -u +%Y-%m-%d).md | wc -l

# Current model
cron list | jq '.jobs[] | select(.name | contains("Layer 0")) | .payload.model'
```

If cost exceeds $1/day:
- Increase interval (reduce frequency)
- Switch to cheaper model

If cost is well under $1/day:
- Decrease interval (increase frequency)
- Switch to higher-quality model

---

## Recommended Profiles

### **High-Frequency (Real-time feel)**
- Model: `openrouter/google/gemini-2.5-flash`
- Interval: 3 minutes
- Cost: ~$0.96/day
- Runs: 480/day
- Use case: Near-instant memory writes, minimal lag

### **Balanced (Current)**
- Model: `anthropic/claude-haiku-4-5`
- Interval: 10 minutes
- Cost: ~$1.00/day
- Runs: 144/day
- Use case: Good balance of cost, quality, responsiveness

### **High-Quality (Deep reasoning)**
- Model: `openai/gpt-4.1`
- Interval: 72 minutes
- Cost: ~$1.00/day
- Runs: 20/day
- Use case: Sophisticated pattern-matching, less frequent writes

---

**Current profile: Balanced (Haiku @ 10 min)**

Change profiles anytime via `cron update`. Budget stays locked at $1/day.
