# Layer 0.5 Pre-Turn Integration Guide

**Status:** Ready to wire. Staging files live at `memory/layer0.5/context-injection-*.json`

---

## Quick Start (For G)

Layer 0.5 is now running silently every 15 minutes, staging semantic recall results. To make them actually appear in your conversation context, we need to wire a pre-turn hook into lossless-claw.

### What it does
Before each message you send, OpenClaw will:
1. Read the latest staging file from `memory/layer0.5/`
2. Extract top 3 relevant memories
3. Prepend them to the context as "Relevant Memories (Semantic Recall)"

### Why you want this
You get instant context on your current priorities and recent work, without it cluttering the chat. Reduces token waste on redundant context-building.

---

## Integration Options

### Option A: lossless-claw Plugin Hook (Recommended)
**Complexity:** Low | **Latency:** ~100ms | **Cost:** Free

If lossless-claw v0.5.2+ supports pre-expansion hooks:

```json
{
  "plugins": {
    "entries": {
      "lossless-claw": {
        "config": {
          "preExpansionHook": {
            "enabled": true,
            "scriptPath": "/data/.openclaw/workspace/scripts/layer0.5-hook.js",
            "stagingDir": "/data/.openclaw/workspace/memory/layer0.5",
            "maxResults": 3
          }
        }
      }
    }
  }
}
```

**Implementation:**
1. Create `/data/scripts/layer0.5-hook.js` (see below)
2. Update openclaw.json (plugin config above)
3. Restart gateway: `openclaw gateway restart`

### Option B: Sidecar File Reading (Fallback)
**Complexity:** Medium | **Latency:** ~50ms | **Cost:** Free

lossless-claw reads staging files at context build time:

```javascript
// In lossless-claw's context pre-processor:
const fs = require('fs');
const path = require('path');

async function readLatestInjection() {
  const dir = '/data/.openclaw/workspace/memory/layer0.5';
  const files = fs.readdirSync(dir)
    .filter(f => f.startsWith('context-injection-'))
    .sort()
    .reverse();
  
  if (!files.length) return null;
  
  const latest = JSON.parse(fs.readFileSync(path.join(dir, files[0])));
  return latest.context_markdown;  // Just the markdown, lossless-claw handles formatting
}
```

**Implementation:**
1. Modify lossless-claw's pre-expansion hook (if available)
2. Call `readLatestInjection()` and prepend result to context

### Option C: Manual System Event (Simplest)
**Complexity:** Low | **Latency:** ~1s | **Cost:** Free

Use a cron job to inject staged memories as system events:

```javascript
// Runs every 30 seconds, updates a "current context" system event
const latestInjection = readLatestFile('memory/layer0.5/context-injection-*.json');
const systemMessage = {
  role: "system",
  content: `## Current Semantic Context\n${latestInjection.context_markdown}`
};
// Inject into current session via OpenClaw API
```

**Implementation:**
1. Create `/data/scripts/system-event-injector.js`
2. Add cron job (30s interval) that reads staging files and posts to OpenClaw events API
3. No config changes needed

---

## Example Hook Script (Option A)

Save this as `/data/.openclaw/workspace/scripts/layer0.5-hook.js`:

```javascript
#!/usr/bin/env node
/**
 * Layer 0.5 Pre-Turn Hook for lossless-claw
 * 
 * Runs before context expansion.
 * Reads latest staging file and injects relevant memories.
 */

const fs = require('fs');
const path = require('path');

const STAGING_DIR = '/data/.openclaw/workspace/memory/layer0.5';
const MAX_RESULTS = 3;

function readLatestStaging() {
  try {
    const files = fs.readdirSync(STAGING_DIR)
      .filter(f => f.startsWith('context-injection-'))
      .sort()
      .reverse();
    
    if (!files.length) return null;
    
    const latest = fs.readFileSync(
      path.join(STAGING_DIR, files[0]),
      'utf-8'
    );
    return JSON.parse(latest);
  } catch (err) {
    console.error(`[L0.5-hook] Read error: ${err.message}`);
    return null;
  }
}

function injectIntoContext(contextBuffer, injection) {
  if (!injection || !injection.context_markdown) return contextBuffer;
  
  // Prepend semantic recall before existing context
  const header = `\n## Semantic Recall (Layer 0.5)\n*Confidence: ${(injection.confidence * 100).toFixed(0)}%*\n`;
  return header + injection.context_markdown + '\n\n' + contextBuffer;
}

module.exports = {
  // lossless-claw hook interface
  preExpansion: async (contextBuffer, metadata) => {
    const injection = readLatestStaging();
    if (!injection || injection.results_count === 0) {
      return contextBuffer; // No results, pass through
    }
    
    return injectIntoContext(contextBuffer, injection);
  },
  
  // Test mode
  test: () => {
    const inj = readLatestStaging();
    console.log('Latest staging:', inj ? 'OK' : 'EMPTY');
    if (inj) {
      console.log(`  Results: ${inj.results_count}`);
      console.log(`  Confidence: ${inj.confidence}`);
      console.log(`  Markdown length: ${inj.context_markdown.length}`);
    }
  }
};
```

**Test:**
```bash
node /data/.openclaw/workspace/scripts/layer0.5-hook.js
```

---

## Configuration

### openclaw.json Patch (Option A)

If using the plugin hook method, add this to plugins.entries.lossless-claw:

```json
{
  "config": {
    "freshTailCount": 32,
    "contextThreshold": 0.75,
    "summaryModel": "anthropic/claude-haiku-4-5",
    "expansionModel": "anthropic/claude-haiku-4-5",
    "preExpansionHook": {
      "enabled": true,
      "scriptPath": "/data/.openclaw/workspace/scripts/layer0.5-hook.js",
      "timeout": 5000
    }
  }
}
```

Apply via:
```bash
# Backup first
cp /data/.openclaw/openclaw.json /data/.openclaw/openclaw.json.backup

# Apply config
gateway config.patch --path "plugins.entries.lossless-claw.config.preExpansionHook" \
  --raw '{"enabled": true, "scriptPath": "/data/.openclaw/workspace/scripts/layer0.5-hook.js"}'

# Restart
gateway restart --note "Layer 0.5 pre-turn hook enabled"
```

---

## Validation Checklist

- [ ] Staging files present: `ls memory/layer0.5/context-injection-*.json`
- [ ] Latest file is fresh: `stat memory/layer0.5/context-injection-*.json | grep Modify`
- [ ] Cron job running: `cron list | grep "Layer 0.5"`
- [ ] Hook script exists (if Option A): `test -f scripts/layer0.5-hook.js`
- [ ] Config applied (if Option A): `gateway config.get | grep preExpansionHook`
- [ ] Gateway restarted: `openclaw status`
- [ ] Test message sent: Verify semantic context appears in chat

---

## Example Output (After Integration)

When you send a message, you'll see:

```
## Semantic Recall (Layer 0.5)
*Confidence: 70%*

### [1] memory/projects/career-transition.md (chunk 0/1, score=0.417)
*From memory_projects*

# Project — Career Transition
## ⚠️ TOP PRIORITY — THIS IS THE MOST IMPORTANT ACTIVE PROJECT

(... truncated memory text ...)

## [2] memory/daily/2026-04-03.md (chunk 0/1, score=0.490)
*From memory_daily*

## Heartbeat signals
- [project] [critical] The `gog` tool is not installed...
```

This appears **before** your message is processed, giving context to the model.

---

## Monitoring & Tuning

### Check sidecar health
```bash
# Last 10 sidecar runs
tail -100 /data/.openclaw/workspace/memory/layer0.5/*.json

# Cron job status
cron runs --jobId 212e8a54-f5e8-4b1a-b14d-118ffd45d74b
```

### Adjust ranking
If context feels stale, boost recency in `scripts/layer0.5-cron.py`:

```python
# Current boosting:
# - Today: +0.15
# - This week: +0.10
# - This month: +0.05

# To make it more aggressive:
# - Today: +0.25
# - This week: +0.15
```

### Change search collections
In `scripts/layer0.5-cron.py`:

```python
# Current default (line ~60):
collections = ["memory_self", "memory_projects", "memory_daily"]

# To include all:
collections = ["memory_self", "memory_projects", "memory_lessons", "memory_daily", "memory_semantic"]
```

---

## Troubleshooting

### Staging files not being created
```bash
# Run cron manually
python3 /data/.openclaw/workspace/scripts/layer0.5-cron.py

# Check output
ls -la memory/layer0.5/
tail -20 memory/daily/$(date +%Y-%m-%d).md | grep "L0.5"
```

### Hook not injecting
```bash
# Check config applied
gateway config.get | grep -A5 preExpansionHook

# Check for errors in gateway logs
tail -100 /var/log/openclaw/gateway.log | grep -i layer
```

### Semantic results are irrelevant
This means the query embedding is poor or Qdrant needs more data. Check:
```bash
# Test Layer 0.5 CLI directly
python3 scripts/context-injection-layer0.5.py --query "your question here"

# Verify Qdrant has data
curl http://localhost:6333/collections | jq '.result[] | {name: .name, points_count: .points_count}'
```

---

## Cost & Performance

- **Sidecar cost:** ~$0.02/day (30 Layer 0.5 CLI calls, ~$0.0006 each)
- **Hook latency:** <100ms (file read + JSON parse)
- **Context overhead:** ~300–500 tokens per injection (3 memories)
- **Net benefit:** Avoids ~2–3 rounds of redundant context-building per session

---

## Next Steps (G's Decision)

1. **Choose integration method** (A/B/C above)
2. **Deploy hook script** (if A or C)
3. **Update openclaw.json** (if A)
4. **Restart gateway**
5. **Test:** Send a message, verify semantic context appears
6. **Tune:** Adjust recency boosting or collection filters as needed

---

**Ready to proceed?** Let me know which option you prefer and I'll wire it up.

Sent: April 3, 2026, 05:30 EDT
