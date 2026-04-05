# Lessons — Systems

Workarounds, gotchas, and operational solutions for tools and infrastructure.

---

## WhatsApp Gateway (Tailscale + Paired Node)

**Issue [2026-04-04 05:45 UTC]:** Gateway reconnection failures (5 bounces in prior hour)
**Resolution:** Gateway now stable and confirmed connected as +15307104559
**Lesson:** Gateway can bounce briefly during reconnection cycles. Monitor the output of `whatsapp_login status` or check recent gateway logs before attempting send.
**Applied pattern:** After reconnection bounces, wait ~3–5 minutes before retrying external communications.

---

## Gmail / `gog` Tool

**Status [2026-04-04 14:52 UTC]:** Gmail OAuth token (Maton/gog integration) REVOKED — job email monitoring BLOCKED.
**Fallback:** `himalaya` IMAP skill available; supports multiple accounts and message search.
**Remediation:** Immediate switch to `himalaya` IMAP monitoring required — OAuth re-auth not expected before Batch 2.
**Timeline:** Hard deadline for migration: April 7 (Batch 2 job outreach).

---

## OpenClaw Binary Staleness

**Problem:** /usr/local/bin/openclaw → 2026.3.12 (stale)
**Current:** /data/.npm-global/bin/openclaw → 2026.3.23-2
**Lesson:** Always use explicit path for diagnostics: `/data/.npm-global/bin/openclaw [command]` to avoid stale binary issues.

