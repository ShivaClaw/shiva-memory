# Layer 0 Signal Router — Enhanced with Semantic Recall

**Status:** Ready for integration into main AGENT-PROMPT.md
**Approach:** Inline semantic context into Layer 0 signal detection (no separate injection needed)

---

## Concept

Instead of running Layer 0.5 as a separate sidecar, integrate semantic recall **into** Layer 0's signal detection loop. This way:

1. Layer 0 runs every 15 minutes (existing Haiku agent)
2. Before processing signals, it reads latest Layer 0.5 staging file
3. Prepends semantic context to its system prompt
4. Routes signals + context together into `memory/layer0/last-run.md`

Result: Every Layer 0 run includes recent semantic context without extra systems.

---

## Integration Pattern

### Before (Current)
```
Layer 0 Cron (every 15min)
├─ Read daily log
├─ Detect signals
├─ Classify + route
└─ Write to memory/layer0/last-run.md
```

### After (With Semantic Context)
```
Layer 0 Cron (every 15min)
├─ Read latest Layer 0.5 staging file
├─ Read daily log
├─ Prepend semantic context to system prompt
├─ Detect signals
├─ Classify + route
└─ Write to memory/layer0/last-run.md (with context annotation)
```

---

## Modified AGENT-PROMPT Snippet

Add to Layer 0's system prompt (in AGENT-PROMPT.md):

```markdown
## Context Injection (Layer 0.5)

Recent semantic recall:
---
{LAYER_0_5_CONTEXT_MARKDOWN}
---

Use this context when classifying signals. If you detect signals related to the injected memories (e.g., job search status updates when job-search context is available), flag them with priority boost.
```

Placeholder `{LAYER_0_5_CONTEXT_MARKDOWN}` gets replaced by the cron job before sending to Haiku.

---

## Implementation Steps

1. **Modify Layer 0 cron script** to:
   - Read `/data/.openclaw/workspace/memory/layer0.5/context-injection-*.json` (latest file)
   - Extract `context_markdown` field
   - Substitute into AGENT-PROMPT system prompt
   - Send augmented prompt to Haiku

2. **Update AGENT-PROMPT.md** to include the placeholder section above

3. **Test:** Run cron, verify Layer 0 runs with semantic context included

---

## Pros & Cons

**Pros:**
- ✅ No separate system event injection (cleaner chat)
- ✅ Semantic context is part of Layer 0 output (auditable)
- ✅ Context-aware signal routing (higher quality)
- ✅ No additional API calls or crons

**Cons:**
- ⚠️ Requires modifying AGENT-PROMPT.md
- ⚠️ Adds ~300–500 tokens to each Layer 0 run (~$0.0002 per run)

---

## Ready to Wire?

Once you approve, I'll:
1. Update AGENT-PROMPT.md with semantic context placeholder
2. Create wrapper script that Layer 0 cron calls (reads staging + substitutes context)
3. Test end-to-end
4. Commit to GitHub

This keeps the architecture simple: Layer 0.5 stages context, Layer 0 consumes it.

---

**Alternative:** If you prefer Option A (lossless-claw plugin hook), I can wait for lossless-claw v0.5.3+ which may support it, or we can implement Option C (system event injection to chat) if you want semantic context visible in every turn.

**Decision needed:** Inline into Layer 0 (recommended), wait for plugin hook, or inject as chat events?
