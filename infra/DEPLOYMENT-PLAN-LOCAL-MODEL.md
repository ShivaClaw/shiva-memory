# Local Model Deployment Plan — Ollama + Atlas Test

**Objective:** Deploy local LLM fallback (qwen2.5:14b via Ollama) with crash-test-dummy validation via Atlas before connecting to Shiva.

**Date:** 2026-04-02  
**Model:** qwen2.5:14b (8GB RAM, solid reasoning)  
**VPS Resources:** 16GB RAM, 4 cores, 193GB disk

---

## Phase 1: Deploy Ollama

**Files:**
- `docker-compose-ollama.yml` (Ollama + Traefik route)

**Steps:**
1. Deploy Ollama container:
   ```bash
   docker compose -f docker-compose-ollama.yml up -d
   ```
2. Pull qwen2.5:14b model:
   ```bash
   docker exec -it ollama ollama pull qwen2.5:14b
   ```
3. Verify model loaded:
   ```bash
   docker exec -it ollama ollama list
   ```
4. Test Ollama API:
   ```bash
   curl https://ollama.clawofshiva.tech/api/tags
   ```

**Success Criteria:**
- Container running
- Model downloaded (~8GB)
- API responding via Traefik

---

## Phase 2: Deploy Atlas (Crash Test Dummy)

**Files:**
- `docker-compose-atlas.yml` (Atlas + Traefik route)

**Steps:**
1. Deploy Atlas container:
   ```bash
   docker compose -f docker-compose-atlas.yml up -d
   ```
2. Wait for OpenClaw installation (~2-3 minutes)
3. Check Atlas logs:
   ```bash
   docker logs atlas -f
   ```
4. Verify Atlas gateway reachable:
   ```bash
   curl https://atlas.clawofshiva.tech/health
   ```

**Success Criteria:**
- Container running
- OpenClaw installed
- Gateway responding via Traefik

---

## Phase 3: Connect Atlas → Ollama

**Steps:**
1. SSH into Atlas container:
   ```bash
   docker exec -it atlas /bin/sh
   ```
2. Edit Atlas config (`/data/.openclaw/openclaw.json`), add Ollama provider:
   ```json
   {
     "models": {
       "providers": {
         "ollama": {
           "endpoint": "https://ollama.clawofshiva.tech",
           "models": {
             "qwen2.5:14b": {
               "alias": "Qwen 2.5 14B"
             }
           }
         }
       }
     },
     "agents": {
       "defaults": {
         "model": {
           "primary": "ollama/qwen2.5:14b",
           "fallbacks": ["openai/gpt-5.2"]
         }
       }
     }
   }
   ```
3. Restart Atlas gateway:
   ```bash
   /data/.npm-global/bin/openclaw gateway restart
   ```
4. Test Atlas with Ollama model via web UI or Telegram

**Success Criteria:**
- Atlas responds to prompts
- No crashes or restart loops
- Ollama model inference working

---

## Phase 4: Connect Shiva → Ollama (if Atlas survives)

**Pre-flight:**
1. **Take VPS snapshot** before touching Shiva's config
2. Backup current Shiva config:
   ```bash
   cp /data/.openclaw/openclaw.json /data/.openclaw/openclaw.json.backup-pre-ollama
   ```

**Steps:**
1. Add Ollama to Shiva's config (same structure as Atlas test)
2. Set as **fallback only** initially (keep API providers primary):
   ```json
   {
     "agents": {
       "defaults": {
         "model": {
           "primary": "openai/gpt-5.2",
           "fallbacks": ["ollama/qwen2.5:14b", "anthropic/claude-haiku-4-5"]
         }
       }
     }
   }
   ```
3. Restart Shiva gateway:
   ```bash
   /data/.npm-global/bin/openclaw gateway restart
   ```
4. Monitor logs for errors:
   ```bash
   /data/.npm-global/bin/openclaw logs -f
   ```
5. Test Ollama fallback by temporarily blocking API provider (optional)

**Success Criteria:**
- Shiva stable
- Ollama fallback working when API providers unavailable
- No memory/CPU spikes

---

## Rollback Plan

If Atlas or Shiva breaks:
1. **Atlas:** Delete container, redeploy fresh
   ```bash
   docker compose -f docker-compose-atlas.yml down -v
   ```
2. **Shiva:** Restore config backup + VPS snapshot if needed
   ```bash
   cp /data/.openclaw/openclaw.json.backup-pre-ollama /data/.openclaw/openclaw.json
   /data/.npm-global/bin/openclaw gateway restart
   ```

---

## Resource Monitoring

Monitor during deployment:
```bash
docker stats --no-stream
free -h
```

Expected Ollama RAM usage: ~8-10GB when loaded, ~1GB idle.

---

**Next Step:** Run Phase 1 (deploy Ollama + pull model).
