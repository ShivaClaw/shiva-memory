# Backup & Recovery Strategy

**Created:** 2026-04-02T00:13:00Z  
**Updated:** 2026-04-02T00:14:00Z  
**Status:** Active Deployment

---

## Overview

Two-layer backup system protecting against total system failure:

1. **Layer A: VPS Snapshots (Hostinger Native)** — Full system state every 24 hours
2. **Layer B: Docker Compose + Metadata (GitHub)** — Configuration reproducibility every 72 hours + on-demand

Both layers are automated, encrypted where sensitive, and designed for rapid recovery.

---

## Layer A: Hostinger VPS Snapshots

### What Gets Backed Up
- Full VPS OS state (Ubuntu 22.04)
- All Docker containers (OpenClaw, Traefik, Qdrant, FalkorDB, etc.)
- Volumes and persistent data (LCM SQLite, Layer 0 logs, memory files)
- Network configuration
- DNS records

### Schedule
- **Daily:** 03:00 MDT (after Layer 2 GitHub backup, before US business hours)
- **On-demand:** Triggered manually before major changes (updates, deployments)

### Cadence
- 1 snapshot per VM (Hostinger overwrites on each create)
- Retention: 20 days from creation (confirmed from API response 2026-04-02; `expires_at` field)
- Restore time: ~30 minutes (`restore_time: 1800` seconds from API)

### Implementation
- **Cron:** `Hostinger VPS Snapshot (Daily)` — Claude Haiku + Hostinger API
- **Job name:** Includes `HOSTINGER_API_TOKEN` reference from local `.enc` file
- **API endpoint:** `https://developers.hostinger.com/api/vps/v1/virtual-machines/{virtualMachineId}/snapshot` ✅ (corrected 2026-04-02; old URL caused HTTP 530)
- **Note:** Hostinger keeps only 1 snapshot per VM — each new snapshot overwrites the previous
- **Failure handling:** WhatsApp alert if snapshot fails; retry every 15 min for 2 hours

### Recovery Path
```bash
# 1. In Hostinger hPanel, select snapshot
# 2. Restore to same VPS or new VPS
# 3. Wait for boot (5–10 min)
# 4. SSH in, verify container status
# 5. Done
```

### Cost
- Hostinger VPS plan includes 2 free snapshots; additional at $0.50–$1.00 each
- 1 snapshot per VM (overwrites) → minimal cost; 20-day retention window

---

## Layer B: Docker Compose + Metadata (GitHub)

### What Gets Backed Up
- Current `docker-compose.yml` (live configuration)
- `.env.example` (template, no secrets)
- `Dockerfile` + build context (if custom images)
- Qdrant collection schemas (as `.json` exports)
- FalkorDB graph schemas (as `.yaml` exports)
- Layer 0 agent prompt + cost tuning profiles
- Cron definitions (payload + schedule metadata)
- Recovery runbook

### What Does NOT Get Backed Up
- API keys, tokens, passwords (referenced via `TOKENS&KEYS` sheet only)
- Private SSH keys (stored locally on VPS)
- Sensitive credentials (use Hostinger snapshot for full state)

### Schedule
- **Every 72 hours:** Sunday 05:00 MDT (after VPS snapshot at 03:00)
- **On-demand:** Before major changes (deployments, plugin updates, config rewrites)
- **Before updates:** Always commit compose state before running `openclaw update`

### Implementation
- **Cron:** `GitHub Compose Backup (72h + on-demand)` — Claude Sonnet 4.5 + git CLI
- **Repo:** `ShivaClaw/shiva-infra` (private)
- **Branch:** `main` (default) + `deploy-compose-files` (staging)
- **Commit message:** `backup(compose): $(date +%Y-%m-%d-%H:%M) - [VPS_STATE]`
- **Auth:** SSH key (`~/.ssh/id_ed25519`)
- **Failure handling:** WhatsApp alert + retry queue

### Directory Structure (in repo)
```
shiva-infra/
├── docker-compose.yml           # Current live config
├── docker-compose.prod.yml      # Tagged versions (dated)
├── .env.example                 # Template (secrets reference TOKENS&KEYS)
├── schemas/
│   ├── qdrant-collections.json  # Vector search schema
│   └── falkordb-graph.yaml      # Graph memory schema
├── crons/
│   ├── layer0-agent-prompt.md
│   ├── update-protocol.md
│   └── cost-tuning-profiles.md
├── recovery/
│   ├── RUNBOOK.md               # Step-by-step restore procedure
│   ├── vps-snapshot-restore.md
│   └── compose-restore.md
└── backups/
    ├── compose-2026-04-02.yml
    ├── compose-2026-04-05.yml
    └── ...
```

### Recovery Path
```bash
# 1. Clone repo
git clone git@github.com:ShivaClaw/shiva-infra.git

# 2. Inspect the desired compose version
cat docker-compose.yml
# or
cat backups/compose-2026-03-30.yml

# 3. Set environment variables (from TOKENS&KEYS spreadsheet)
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
# ... etc

# 4. Pull and start
docker-compose pull
docker-compose up -d

# 5. Wait for health checks (~2 min)
docker-compose ps
```

---

## Failure Modes & Recovery

### Scenario 1: Gateway Dies But Containers Still Run
**Detection:** OpenClaw chat loads but "Failed to connect to model provider"

**Recovery:**
1. SSH into VPS
2. Check container status: `docker ps`
3. If containers healthy: Restart gateway plugin
4. If containers unhealthy: Hostinger snapshot restore

### Scenario 2: VPS Completely Down (Hardware Failure)
**Detection:** Can't SSH, can't access hPanel

**Recovery:**
1. Log into Hostinger hPanel
2. Select "Snapshots" from VPS menu
3. Choose most recent snapshot
4. Click "Restore to this VPS" or "Restore to New VPS"
5. Wait 5–10 minutes for boot
6. SSH in, verify with `docker ps`

### Scenario 3: Accidental Container Deletion
**Detection:** A container is missing but others are fine

**Recovery:**
1. Clone `shiva-infra` repo
2. `docker-compose pull` (refresh images)
3. `docker-compose up -d <service_name>` (restart specific container)
4. Monitor logs: `docker logs -f <container>`

### Scenario 4: Data Corruption in LCM or Memory
**Detection:** Weird behavior in Layer 0 or memory files

**Recovery:**
1. Hostinger snapshot restores full data
2. Fallback: GitHub compose + manual data re-entry (unlikely; LCM backups to Layer 2 daily)

---

## Cron Jobs Implementing Backup

### Cron 1: Hostinger VPS Snapshot (Daily @ 03:00 MDT)

**Name:** `Hostinger VPS Snapshot (Daily)`  
**Schedule:** `0 3 * * * America/Denver`  
**Model:** Claude Haiku 4.5  
**Payload:**
```json
{
  "kind": "agentTurn",
  "message": "Snapshot the current VPS state via Hostinger API. Use HOSTINGER_API_TOKEN from /data/.openclaw/workspace/memory/infra/HOSTINGER_CREDENTIALS.enc. Keep last 7 snapshots. Report success or failure."
}
```

**Delivery:** WhatsApp announce on failure only

**Cost:** ~$0.002/run × 1/day = $0.06/month

---

### Cron 2: GitHub Compose Backup (72h + on-demand @ 05:00 MDT Sunday)

**Name:** `GitHub Compose Backup (72h + on-demand)`  
**Schedule:** `0 5 * * 0 America/Denver` (Sundays)  
**Model:** Claude Sonnet 4.5  
**Payload:**
```json
{
  "kind": "agentTurn",
  "message": "Export current docker-compose.yml, .env.example, and schema files to ShivaClaw/shiva-infra repo. Commit with timestamp + VPS state summary. Use SSH key at ~/.ssh/id_ed25519. Verify push success."
}
```

**Delivery:** WhatsApp announce on success + failure

**Cost:** ~$0.05/run × 1/week = $0.20/month

---

## Implementation Status

**Completed (2026-04-02T00:15:00Z):**
- [x] Backup architecture designed
- [x] Recovery runbooks written (7625 bytes + 8704 bytes)
- [x] Cron jobs created:
  - `Hostinger VPS Snapshot (Daily @ 03:00 MDT)` — ID `b89be62d-eb0c-4ce4-9565-4370fb7d592d`
  - `GitHub Compose Backup (Weekly Sunday @ 05:00 MDT)` — ID `aa211fa3-6df5-4c64-81e3-17838b316734`
- [x] Docker Compose template created (`infra/docker-compose.yml`)
- [x] Environment variable template created (`infra/.env.example`)
- [x] Recovery README created (`infra/README.md`)
- [x] HOSTINGER_API_TOKEN stored locally (`memory/infra/HOSTINGER_CREDENTIALS.enc`)
- [x] Local git commit: `8c7810e backup(infra)...`

**In Progress:**
- [ ] Push infra files to `ShivaClaw/shiva-infra` repo (needs repo creation + remote setup)
- [ ] Document VPS ID from Hostinger hPanel
- [ ] Test Hostinger API snapshot (manual trigger in hPanel first)

**Pending G's Input:**
- [ ] Provide Hostinger VPS ID (from hPanel → VPS settings)
- [ ] Create `shiva-infra` private GitHub repo (or authorize me to)
- [ ] First manual snapshot test in Hostinger hPanel (non-cron)

---

## Reference Data

**HOSTINGER_API_TOKEN:** Stored in `/data/.openclaw/workspace/memory/infra/HOSTINGER_CREDENTIALS.enc` (do not share)

**Hostinger VPS ID:** `1489775` ✅  
**VPS hostname:** openclaw.trident-memory.com (planned)  
**Hostinger account email:** brandongkirksey@gmail.com  
**GitHub repos:**  
  - `ShivaClaw/shiva-memory` — Core identity + memory files (active)
  - `ShivaClaw/shiva-infra` — Docker Compose + recovery (ready to push)

**SSH key:** `~/.ssh/id_ed25519` (Ed25519, mode 600)  
**Snapshot retention:** 7 days (rolling window)  
**Compose backup frequency:** Every 72 hours + on-demand + before updates  
**Recovery runbook:** `/data/.openclaw/workspace/memory/projects/RECOVERY_RUNBOOK.md`

---

## Next Steps (By Priority)

1. **Provide VPS ID:** G should get this from Hostinger hPanel and paste it here
2. **Create shiva-infra repo:** G creates private GitHub repo OR authorizes Shiva to create
3. **Test snapshot manually:** G triggers snapshot in hPanel to verify Hostinger API works
4. **First cron run:** Monday 2026-04-03 @ 03:00 MDT (Hostinger snapshot will run automatically)
5. **Verify cron success:** Check WhatsApp for snapshot confirmation
6. **Weekly compose backup:** Sunday 2026-04-07 @ 05:00 MDT (GitHub commit)

---

## Cost Summary

- **Hostinger snapshots:** ~$2.50/month (5 snapshots × $0.50, 7-day rolling window)
- **Cron jobs:** ~$0.10/month (Haiku + Sonnet combined)
- **Total:** ~$2.60/month additional

**Headroom:** Well within budget.

---

## Notes

- Hostinger API token has been isolated in encrypted local file (not in git, not in config)
- TOKENS&KEYS spreadsheet remains canonical source for all credentials
- Recovery procedures tested on paper; recommend monthly practical test (spin up test VPS, restore from backup)
- Both cron jobs report via WhatsApp; no manual intervention needed after VPS ID is configured

