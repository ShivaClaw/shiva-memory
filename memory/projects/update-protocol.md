# OpenClaw Update Protocol

**Created:** 2026-04-02  
**Owner:** Layer 0 / Update Cron  
**Purpose:** Automated weekly update analysis + compatibility assessment

---

## Overview

Every Sunday at 03:00 MDT, an isolated agent:

1. **Checks for updates** (npm registry or GitHub releases)
2. **Fetches changelog/release notes** (if available)
3. **Analyzes compatibility** against current build + custom architecture
4. **Recommends action:**
   - ✅ **Safe to install** → draft install command, ask for approval
   - ⚠️ **Potentially breaking** → flag specific conflicts, suggest waiting or workarounds
   - 🔧 **Incompatible but adaptable** → draft bespoke patch/workaround, recommend manual review
   - ❌ **Skip entirely** → recommend staying on current version with reasoning

---

## Compatibility Criteria

### What We Check

**1. Core Dependencies**
- Node.js version requirements
- npm package conflicts
- Docker base image changes

**2. Config Schema Changes**
- Does `openclaw.json` structure change?
- Are existing plugins still compatible?
- Do cron job schemas change?

**3. Custom Architecture Impact**
- **LCM (lossless-claw plugin):** Schema changes? DB migrations required?
- **Layer 0 cron:** Payload format changes? Model alias changes?
- **Layer 2 GitHub backup:** Git workflow affected?
- **Qdrant + FalkorDB:** Network/proxy changes that could break Traefik routing?

**4. Breaking Changes (Explicit)**
- Changelog mentions "BREAKING"
- Major version bump (x.0.0)
- Plugin API changes
- Tool signature changes

**5. Security Patches**
- CVE fixes (high priority, bias toward install)
- Dependency vulnerabilities

---

## Decision Tree

```
Is there an update available?
├─ NO → Report "No updates available, system current"
└─ YES → Fetch changelog
    │
    ├─ Is it a security patch (CVE mentioned)?
    │   └─ YES → Recommend immediate install (security override)
    │
    ├─ Is it a patch version (x.y.Z)?
    │   ├─ Breaking changes in changelog?
    │   │   ├─ NO → ✅ Safe to install
    │   │   └─ YES → ⚠️ Flag conflicts, suggest workaround
    │   └─ No changelog available?
    │       └─ ✅ Assume safe (patch versions should be non-breaking)
    │
    ├─ Is it a minor version (x.Y.0)?
    │   ├─ Config schema compatible?
    │   │   ├─ YES → Check plugin compatibility
    │   │   │   ├─ All plugins compatible → ✅ Safe to install
    │   │   │   └─ Plugin conflicts → ⚠️ Detail conflicts, suggest disable/replace
    │   │   └─ NO → 🔧 Draft config migration script
    │   └─ No changelog?
    │       └─ ⚠️ Recommend manual review before install
    │
    └─ Is it a major version (X.0.0)?
        ├─ Analyze breaking changes
        │   ├─ Can we adapt our architecture?
        │   │   ├─ YES → 🔧 Draft migration plan (config + crons + scripts)
        │   │   └─ NO → ❌ Recommend skip, detail blockers
        │   └─ No migration path?
        │       └─ ❌ Skip, wait for community feedback or future patch
        └─ Security critical?
            └─ YES → 🔧 Draft workaround + recommend install despite breaking changes
```

---

## Analysis Checklist

For every update candidate, the agent must answer:

### ✅ Go/No-Go Questions
- [ ] Does this require Node.js version change?
- [ ] Does this require Docker base image rebuild?
- [ ] Does this change `openclaw.json` schema?
- [ ] Does this affect plugin APIs we use?
- [ ] Does this change cron payload structure?
- [ ] Does this change tool signatures (exec, cron, message, etc.)?
- [ ] Does this affect LCM database schema?
- [ ] Does this impact network topology (Docker, Traefik)?
- [ ] Does the changelog mention BREAKING or deprecation?
- [ ] Is this a security patch (CVE, vulnerability fix)?

### 🔍 Deep Dive (If Unclear)
- [ ] Read full changelog/release notes
- [ ] Check GitHub issues for reported breakage
- [ ] Compare `openclaw --help` output (current vs. new, if available)
- [ ] Review plugin compatibility matrix (if published)
- [ ] Check OpenClaw Discord/Reddit for community reports

---

## Recommendation Output Format

**Delivered to G via WhatsApp every Sunday 03:00 MDT.**

### Template (Safe Install)

```
🔔 OpenClaw Update Available

Current: v2026.3.23-2
Latest:  v2026.4.6

Type: Patch (non-breaking)
Changelog: https://github.com/openclaw/openclaw/releases/tag/v2026.4.6

Summary:
- Fixed LCM compaction edge case
- Improved cron scheduler reliability
- Updated dependencies (security patches)

Compatibility: ✅ SAFE TO INSTALL
- No config changes required
- All plugins compatible
- No breaking changes detected

Recommendation: Install now
Command ready:
```bash
/data/.npm-global/bin/openclaw update && openclaw gateway restart
```

Approve? Reply /approve or defer.
```

---

### Template (Breaking Changes)

```
⚠️ OpenClaw Update Available (Breaking Changes)

Current: v2026.3.23-2
Latest:  v2026.4.0

Type: Major (BREAKING)
Changelog: https://github.com/openclaw/openclaw/releases/tag/v2026.4.0

Summary:
- NEW: Unified plugin API v2 (old API deprecated)
- BREAKING: Cron payload structure changed
- BREAKING: `openclaw.json` schema version bump

Compatibility: 🔧 ADAPTABLE WITH CHANGES
- lossless-claw: Needs upgrade to v2.x (available)
- Layer 0 cron: Payload structure must be rewritten
- Config: Requires migration script

Conflicts Detected:
1. Cron payload field `message` → renamed to `prompt`
2. Plugin config `plugins.entries` → now `plugins.v2`

Recommendation: Draft migration, test in isolated container first

Migration Plan:
1. Backup current config + DB
2. Upgrade lossless-claw plugin
3. Rewrite Layer 0 cron payload (draft attached)
4. Run config migration script (draft attached)
5. Test in Docker container before live deploy

Approve migration? Reply with decision.
```

---

### Template (Skip Entirely)

```
❌ OpenClaw Update Available (Incompatible)

Current: v2026.3.23-2
Latest:  v2026.5.0

Type: Major (BREAKING, no migration path)
Changelog: https://github.com/openclaw/openclaw/releases/tag/v2026.5.0

Summary:
- Complete rewrite of memory subsystem (replaces LCM)
- Deprecated: lossless-claw plugin (no v2 available)
- New memory backend requires PostgreSQL (not SQLite)

Compatibility: ❌ INCOMPATIBLE
- Our entire memory architecture (LCM + Layer 0 + GitHub) depends on lossless-claw
- No migration tool provided
- Community reports data loss during upgrade

Blockers:
1. lossless-claw has no v2 plugin (abandoned?)
2. New memory backend incompatible with current Layer 0 design
3. PostgreSQL dependency adds complexity + cost

Recommendation: SKIP THIS UPDATE
- Stay on v2026.3.23-2 until migration path emerges
- Monitor for community forks or backports
- Revisit in 2-4 weeks

Alternative: Wait for v2026.5.1 patch (may include LCM compatibility layer)
```

---

## Bespoke Patch Workflow

If update is incompatible but critical (e.g., security patch), the agent should:

1. **Identify the specific fix** (commit, patch, or feature)
2. **Extract the minimal changeset** needed
3. **Draft a standalone patch script** that applies only the fix to current version
4. **Test in isolated environment** (if possible)
5. **Deliver patch + instructions** to G for manual review/apply

**Example:**
```bash
# Bespoke patch for CVE-2026-1234 (applies to v2026.3.x without full upgrade)
cd /data/.npm-global/lib/node_modules/openclaw
wget https://patch-url/cve-2026-1234.patch
git apply cve-2026-1234.patch
openclaw gateway restart
```

---

## Agent Prompt (For Weekly Cron)

```
You are the OpenClaw Update Analyst. Execute this protocol:

1. Check for updates:
   - Run: `/data/.npm-global/bin/openclaw status` (get current version)
   - Query npm: `npm view openclaw version` (get latest)
   - If versions match → report "No updates" and exit

2. Fetch changelog:
   - URL: `https://github.com/openclaw/openclaw/releases/tag/v[VERSION]`
   - Use `web_fetch` to retrieve release notes
   - If unavailable, check `npm view openclaw --json` for metadata

3. Analyze compatibility:
   - Read `/data/.openclaw/workspace/memory/projects/update-protocol.md` (this file)
   - Follow decision tree
   - Check all compatibility criteria

4. Classify update:
   - ✅ Safe to install
   - ⚠️ Potentially breaking
   - 🔧 Incompatible but adaptable
   - ❌ Skip entirely

5. Draft recommendation:
   - Use appropriate template from update-protocol.md
   - Include specific conflicts/migrations if needed
   - Provide ready-to-run commands or scripts

6. Deliver via WhatsApp:
   - Send full analysis + recommendation
   - Do NOT auto-install without explicit approval

7. Log analysis:
   - Append to `memory/projects/update-history.md`:
     ```
     ## [DATE] — v[OLD] → v[NEW]
     - Type: [patch/minor/major]
     - Decision: [safe/breaking/skip/bespoke]
     - Reasoning: [brief summary]
     - Action taken: [installed / deferred / patched]
     ```

Exit with: "Update analysis complete. Recommendation delivered."
```

---

## Edge Cases

**No changelog available:**
- Assume `patch` = safe, `minor` = review needed, `major` = skip until documented

**Community reports breaking:**
- Check r/openclaw, Discord, GitHub issues for user reports
- If widespread breakage reported → recommend skip regardless of changelog

**Security vs. stability tradeoff:**
- Security patches override breaking change concerns
- Draft migration + recommend install with rollback plan

**Plugin abandonment:**
- If critical plugin (lossless-claw) has no compatible version → recommend skip or fork plugin

---

## Rollback Plan (Always Included)

Every install recommendation must include rollback instructions:

```bash
# Rollback to previous version if update breaks
npm install -g openclaw@2026.3.23-2
openclaw gateway restart
```

Backup before update:
```bash
# Snapshot current state
cp -r /data/.openclaw /data/.openclaw.backup-$(date +%Y%m%d)
tar czf /data/openclaw-backup-$(date +%Y%m%d).tar.gz /data/.npm-global/lib/node_modules/openclaw
```

---

## Status

**Last update check:** Not yet configured  
**Next scheduled check:** Sunday 03:00 MDT (once cron created)  
**Current version:** 2026.3.23-2  
**Auto-install enabled:** NO (requires manual approval)

---

_This protocol ensures updates are vetted, compatible, and never surprise-break the system._
