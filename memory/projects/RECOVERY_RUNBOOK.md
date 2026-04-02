# Recovery Runbook

**Created:** 2026-04-02T00:14:00Z  
**Purpose:** Step-by-step procedures to restore from any failure mode

---

## Quick Reference

| Scenario | Time to Recover | Tool | Steps |
|----------|-----------------|------|-------|
| Container crashed | 2–5 min | Docker CLI | 3 |
| Gateway down (containers OK) | 5–10 min | Docker CLI + SSH | 4 |
| Data corruption | 30 min | Hostinger snapshot | 5 |
| Full VPS failure | 10–15 min | Hostinger hPanel | 6 |
| Accidental deletion | 5 min | GitHub + Docker | 4 |

---

## Procedure 1: Container Crashed (Easiest)

**Symptoms:** One container not running; others healthy.  
**Example:** Qdrant crashed but OpenClaw still responsive.

### Steps

1. **SSH into VPS**
   ```bash
   ssh root@<vps-ip>
   ```

2. **Check container status**
   ```bash
   docker ps | grep qdrant
   # or
   docker-compose ps
   ```

3. **Restart the container**
   ```bash
   cd /data/.openclaw/workspace
   docker-compose restart qdrant
   # or for one-time restart
   docker restart <container-id>
   ```

4. **Monitor for 30 seconds**
   ```bash
   docker-compose ps
   docker logs -f qdrant | head -20
   ```

5. **Done.** Container should be running.

---

## Procedure 2: Gateway Down (Containers Running)

**Symptoms:** OpenClaw chat loads but "Failed to connect to model provider" or "Gateway not responding".  
**Root cause:** Gateway plugin crashed but containers are fine.

### Steps

1. **SSH into VPS**
   ```bash
   ssh root@<vps-ip>
   ```

2. **Check OpenClaw container status**
   ```bash
   docker-compose ps openclaw
   ```

3. **Restart OpenClaw gateway**
   ```bash
   cd /data/.openclaw/workspace
   docker-compose restart openclaw
   ```

4. **Wait 30 seconds for startup**
   ```bash
   sleep 30
   docker logs -f openclaw | head -20
   ```

5. **Test connectivity**
   - Open OpenClaw Chat
   - Send a simple message
   - Verify model response

6. **Done.**

### If Still Broken
Jump to **Procedure 3** (data corruption recovery).

---

## Procedure 3: Data Corruption / Persistent Errors

**Symptoms:** Weird behavior, repeated errors, memory not updating, or Layer 0 stuck.  
**Root cause:** Data inconsistency or corrupt SQLite/files.

### Step-by-Step

1. **SSH into VPS**
   ```bash
   ssh root@<vps-ip>
   ```

2. **Stop all containers gracefully**
   ```bash
   cd /data/.openclaw/workspace
   docker-compose down
   ```

3. **Backup current data (just in case)**
   ```bash
   tar -czf /tmp/data-backup-$(date +%s).tar.gz /data/.openclaw/
   ```

4. **Delete corrupted data selectively**
   ```bash
   # LCM database (most likely culprit)
   rm -f ~/.openclaw/lcm.db
   
   # OR Layer 0 state (if Layer 0 is stuck)
   rm -f /data/.openclaw/workspace/memory/layer0/last-run.md
   
   # DO NOT DELETE memory/ folder—only specific corrupted files
   ```

5. **Restart containers**
   ```bash
   docker-compose up -d
   ```

6. **Monitor startup**
   ```bash
   docker-compose ps
   docker logs -f openclaw | tail -50
   ```

7. **Verify functionality**
   - Open OpenClaw Chat
   - Send test message
   - Check memory files were created

8. **Done.** System should reinitialize cleanly.

---

## Procedure 4: Full VPS Failure (Hardware Down)

**Symptoms:** Can't SSH, can't ping, hPanel shows "Offline".  
**Root cause:** VPS crashed or hardware failure.

### Steps

1. **Log into Hostinger hPanel**
   - Go to https://hpanel.hostinger.com
   - Sign in with your credentials
   - Select the VPS

2. **Check power status**
   - If it says "Offline," click "Power On"
   - Wait 60 seconds

3. **If still offline, restore from snapshot**
   - Click "Snapshots" in the VPS menu
   - Select the most recent snapshot (usually today's 03:00 MDT backup)
   - Click "Restore"
   - Wait 5–10 minutes for boot

4. **SSH to verify**
   ```bash
   ssh root@<vps-ip>
   docker ps
   ```

5. **Check container health**
   ```bash
   docker-compose ps
   docker logs openclaw | tail -20
   ```

6. **Done.** System should be running with data from snapshot time.

---

## Procedure 5: Accidental Container Deletion

**Symptoms:** A container is gone (e.g., `docker rm qdrant` was run).  
**Data:** Still intact on disk; just image/config missing.

### Steps

1. **Clone the infra repo**
   ```bash
   cd /tmp
   git clone git@github.com:ShivaClaw/shiva-infra.git
   cd shiva-infra
   ```

2. **Inspect the compose file**
   ```bash
   cat docker-compose.yml | grep -A 10 qdrant
   ```

3. **Pull the image**
   ```bash
   docker pull qdrant/qdrant:latest
   ```

4. **Recreate and start the container**
   ```bash
   cd /data/.openclaw/workspace
   docker-compose up -d qdrant
   ```

5. **Verify**
   ```bash
   docker-compose ps qdrant
   curl http://localhost:6333/health  # If Qdrant
   ```

6. **Done.** Container recreated with same data volumes.

---

## Procedure 6: Need to Move to a New VPS

**Scenario:** Current VPS is being deprecated; need to migrate.

### Steps

1. **Create new VPS at Hostinger**
   - Same OS (Ubuntu 22.04)
   - Same specs or better
   - Note the new IP

2. **SSH into old VPS and snapshot current state**
   ```bash
   ssh root@<old-vps-ip>
   cd /data/.openclaw/workspace
   docker-compose down
   tar -czf /tmp/openclaw-final.tar.gz /data/.openclaw/
   ```

3. **Clone infra repo on old VPS**
   ```bash
   git clone git@github.com:ShivaClaw/shiva-infra.git /tmp/shiva-infra
   ```

4. **SCP the docker-compose and data to new VPS**
   ```bash
   scp /tmp/openclaw-final.tar.gz root@<new-vps-ip>:/tmp/
   scp /tmp/shiva-infra/docker-compose.yml root@<new-vps-ip>:/data/.openclaw/workspace/
   ```

5. **SSH into new VPS and restore**
   ```bash
   ssh root@<new-vps-ip>
   cd /
   tar -xzf /tmp/openclaw-final.tar.gz
   cd /data/.openclaw/workspace
   ```

6. **Set environment variables**
   ```bash
   # Copy from TOKENS&KEYS spreadsheet
   export OPENAI_API_KEY=...
   export ANTHROPIC_API_KEY=...
   # ... etc
   ```

7. **Pull and start**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

8. **Verify**
   ```bash
   docker-compose ps
   docker logs -f openclaw | head -20
   ```

9. **Update DNS** (if applicable)
   - Update any A records pointing to old VPS IP
   - Wait 5–10 min for propagation

10. **Done.** New VPS is now running with all data.

---

## Procedure 7: Restore from GitHub Compose Only (No Snapshot)

**Scenario:** Hostinger snapshot is too old; you want to use GitHub config instead.  
**Data Loss:** Memory files, LCM database — will be empty until Layer 0 rebuilds.  
**Recovery Time:** 2–5 minutes to boot; 10–20 minutes for Layer 0 to catch up.

### Steps

1. **On the new/repaired VPS, clone the repo**
   ```bash
   git clone git@github.com:ShivaClaw/shiva-infra.git
   cd shiva-infra
   ```

2. **Review the compose file**
   ```bash
   cat docker-compose.yml
   ```

3. **Set environment variables**
   ```bash
   export OPENAI_API_KEY=...
   export ANTHROPIC_API_KEY=...
   export HOSTINGER_API_TOKEN=...
   # ... all from TOKENS&KEYS
   ```

4. **Create working directory and pull images**
   ```bash
   mkdir -p /data/.openclaw/workspace
   cd /data/.openclaw/workspace
   cp /path/to/shiva-infra/docker-compose.yml .
   docker-compose pull
   ```

5. **Start all services**
   ```bash
   docker-compose up -d
   ```

6. **Wait for health checks**
   ```bash
   docker-compose ps
   # All should show "Up" after 30 seconds
   ```

7. **Verify OpenClaw gateway**
   - Open OpenClaw Chat
   - Send a test message
   - Check for model response

8. **Layer 0 will rebuild memory**
   - Check `/data/.openclaw/workspace/memory/` folder
   - Layer 0 cron runs every 15 minutes
   - Within 15–20 min, memory files will be recreated

9. **Done.** System is running with fresh memory state.

---

## Emergency Contacts

- **Hostinger Support:** https://hpanel.hostinger.com/support
- **OpenClaw Issues:** https://github.com/openclaw/openclaw/issues
- **Maton API Issues:** https://maton.ai/support

---

## Testing Your Backups (Recommended Monthly)

### Test 1: Hostinger Snapshot Restore (Non-Destructive)
1. Take a manual snapshot in hPanel
2. Create a temporary test VPS (same size)
3. Restore snapshot to test VPS
4. Verify `docker ps` shows all containers
5. Delete test VPS

### Test 2: GitHub Compose Recovery
1. Spin up a blank Ubuntu 22.04 VPS
2. Clone shiva-infra repo
3. Set env vars
4. Run `docker-compose up -d`
5. Verify OpenClaw comes online
6. Delete test VPS

### Test 3: Layer 0 Memory Rebuild
1. Connect to running VPS
2. Delete `/data/.openclaw/workspace/memory/daily/` folder
3. Wait 15 minutes
4. Verify Layer 0 recreated the folder with new files

---

_This runbook is a living document. Update it as recovery procedures are tested and refined._
