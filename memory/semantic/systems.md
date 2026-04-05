# Semantic — Systems

Technical knowledge about tools, infrastructure, and systems I interact with.

---

## OpenClaw

**Version:** 2026.3.23-2 (current at /data/.npm-global/bin/openclaw)
**⚠️ Stale binary:** /usr/local/bin/openclaw → 2026.3.12 — use explicit path for diagnostics
**Config:** /data/.openclaw/openclaw.json
**Workspace:** /data/.openclaw/workspace
**LCM DB:** /data/.openclaw/lcm.db
**Extensions:** /data/.openclaw/extensions/

**Plugins active:**
- lossless-claw 0.5.2 — contextEngine slot, Haiku summarization

**Session config:**
- Idle reset: 43200 min (30 days)
- Heartbeat: every 30m, 07:00–23:00 America/Denver

---

## VPS (Hostinger)

**Environment:** Docker container on Hostinger VPS
**OS:** Linux 6.8.0-106-generic x64
**Resources:** ~14GB available RAM, ~178GB free disk
**Homebrew:** /home/linuxbrew/.linuxbrew

---

## Docker Services (planned)

- Qdrant: ~512MB–1GB RAM, port 6333/6334
- Hindsight: ~512MB–1GB RAM
- FalkorDB: ~512MB RAM

---

## Gmail

**Status [2026-04-04 08:07 UTC]:** ⚠️ **CRITICAL** — `gog` tool not installed, OAuth token revoked.
- Access via `gog` CLI. Always needs explicit env:
```
GOG_KEYRING_PASSWORD=$(cat /data/.openclaw/.gog-keyring-password) GOG_ACCOUNT=brandongkirksey@gmail.com gog gmail ...
```
- Keyring file: /data/.openclaw/.gog-keyring-password
- Fallback: `himalaya` IMAP skill available and fully operational for Gmail email monitoring
- Impact: Blocks career transition project job email monitoring (Batch 2 scheduled April 7)
- Remediation: Re-auth via Maton oauth-gateway OR migrate to himalaya IMAP for response tracking

## WhatsApp Gateway

**Status [2026-04-04 08:07 UTC]:** ✅ **STABLE** — connected as +15307104559
- 5 prior connection bounces RESOLVED
- Current uptime: stable across recent restart cycles
