# Infrastructure Backup & Recovery

**Repository:** `ShivaClaw/shiva-infra` (private)  
**Last Updated:** 2026-04-02T00:15:00Z  
**Status:** Active backup system

---

## Overview

This directory contains:
- Docker Compose configuration template
- Environment variable templates
- Container schemas (Qdrant, FalkorDB)
- Recovery procedures
- Cron job definitions

**Purpose:** Enable rapid recovery of OpenClaw infrastructure from scratch.

---

## Quick Recovery

If the VPS is down and you need to restore:

```bash
# 1. Create a new Ubuntu 22.04 VPS on Hostinger
# 2. Install Docker and Docker Compose
# 3. Clone this repo
git clone git@github.com:ShivaClaw/shiva-infra.git
cd shiva-infra

# 4. Set environment variables
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
# ... (get values from TOKENS&KEYS spreadsheet)

# 5. Start the stack
docker-compose pull
docker-compose up -d

# 6. Verify
docker-compose ps
docker logs -f openclaw
```

**Time to recovery:** ~5 minutes

---

## File Structure

```
infra/
├── README.md                    # This file
├── docker-compose.yml          # Template configuration
├── .env.example                # Environment variable template
├── backups/
│   ├── docker-compose-2026-04-02.yml
│   ├── docker-compose-2026-04-05.yml
│   └── ...                     # Dated backups
├── schemas/
│   ├── qdrant-collections.json
│   └── falkordb-graph.yaml
├── crons/
│   ├── hostinger-snapshot.md
│   ├── github-compose-backup.md
│   └── layer0-agent-prompt.md
└── recovery/
    ├── runbook.md
    ├── vps-snapshot-restore.md
    └── compose-restore.md
```

---

## Backup Schedule

### Hostinger VPS Snapshots (Daily @ 03:00 MDT)
- Full system state backed up to Hostinger
- 7-day rolling retention
- Cron: `Hostinger VPS Snapshot (Daily @ 03:00 MDT)`

**Recovery:** Restore from Hostinger hPanel in 5–10 minutes

### GitHub Compose Backup (Weekly Sunday @ 05:00 MDT)
- Docker Compose config + schemas + cron definitions
- Pushed to `ShivaClaw/shiva-infra`
- Also backed up on major changes (before updates, deployments)

**Recovery:** Clone repo + `docker-compose up -d`

---

## Environment Variables

All sensitive credentials are stored in the **TOKENS&KEYS** Google Sheet (canonical source).

When deploying:
1. Copy `.env.example` to `.env`
2. Fill in values from TOKENS&KEYS
3. Never commit `.env` to git
4. Export vars before `docker-compose up`

Example:
```bash
export OPENAI_API_KEY=$(grep "OPENAI_API_KEY" /path/to/TOKENS&KEYS)
export ANTHROPIC_API_KEY=$(grep "ANTHROPIC_API_KEY" /path/to/TOKENS&KEYS)
# ... etc
```

---

## Hostinger VPS Information

Fill in after creation:

- **VPS ID:** (insert from hPanel)
- **VPS IP:** (insert after creation)
- **Hostname:** openclaw.trident-memory.com
- **OS:** Ubuntu 22.04 LTS
- **Specs:** (as configured)
- **Region:** (as configured)

---

## Testing Your Backups

### Monthly Snapshot Test
1. Create temporary test VPS (same size)
2. Restore latest snapshot to test VPS
3. Verify `docker ps` shows all containers
4. Delete test VPS

### Monthly Compose Test
1. Spin up blank Ubuntu 22.04 VPS
2. Clone this repo
3. Set env vars
4. `docker-compose up -d`
5. Verify all services are healthy
6. Delete test VPS

---

## Troubleshooting

**Docker won't start containers:**
- Check `.env` file has all required keys
- Verify API keys are valid (check TOKENS&KEYS)
- Check disk space: `df -h`
- Check logs: `docker logs <container>`

**Qdrant not accessible:**
- Verify network: `docker network ls | grep traefik`
- Check port: `curl http://localhost:6333/health`
- Check compose labels are correct

**FalkorDB connection refused:**
- Verify container is running: `docker ps | grep falkordb`
- Check port: `redis-cli -p 6379 ping`

**Let's Encrypt certificate issues:**
- Check Traefik logs: `docker logs traefik`
- Verify domain DNS: `nslookup openclaw.trident-memory.com`
- Check email in compose (must be valid)

---

## Disaster Recovery Procedures

See:
- `BACKUP_STRATEGY.md` — Full backup architecture
- `RECOVERY_RUNBOOK.md` — Step-by-step recovery for all scenarios

---

## Cron Jobs Maintaining This System

1. **Hostinger VPS Snapshot (Daily @ 03:00 MDT)**
   - Cron ID: `b89be62d-eb0c-4ce4-9565-4370fb7d592d`
   - Takes a snapshot via Hostinger API
   - Keeps last 7 days
   - WhatsApp alert on failure

2. **GitHub Compose Backup (Weekly Sunday @ 05:00 MDT)**
   - Cron ID: `aa211fa3-6df5-4c64-81e3-17838b316734`
   - Exports docker-compose + schemas
   - Git commits to `ShivaClaw/shiva-infra`
   - WhatsApp alert on failure

---

## Questions?

See:
- Full documentation: `/data/.openclaw/workspace/memory/projects/BACKUP_STRATEGY.md`
- Recovery runbook: `/data/.openclaw/workspace/memory/projects/RECOVERY_RUNBOOK.md`

---

_This system is designed to be resilient. Test it regularly. Update it when you change infrastructure._
