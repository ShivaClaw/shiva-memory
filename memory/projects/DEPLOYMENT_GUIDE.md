# Phase 3b+6 Deployment Guide — Qdrant + FalkorDB

**Architecture:** Two standalone Traefik-integrated services, matching your existing 1-container-per-project pattern.

---

## 1. Qdrant (Vector Search)

**File:** `docker-compose-qdrant.yml`

### Pre-deployment checklist:
- [ ] Replace `qdrant.yourdomain.com` with your actual subdomain
- [ ] Verify `traefik-public` network name matches your setup
- [ ] (Optional) Set `QDRANT__SERVICE__API_KEY` for authentication

### Deploy via Hostinger UI:
1. Create new project: **"memory-qdrant"**
2. Upload `docker-compose-qdrant.yml` as `docker-compose.yml`
3. Deploy
4. Verify: `https://qdrant.yourdomain.com/dashboard`

### Connect from OpenClaw container:

**Via Traefik (external):**
```python
from qdrant_client import QdrantClient
client = QdrantClient(url="https://qdrant.yourdomain.com")
```

**Via Docker network (internal, faster):**
```python
client = QdrantClient(url="http://memory-qdrant:6333")
```

**Recommended:** Use internal Docker network for production (lower latency, no SSL overhead).

---

## 2. FalkorDB (Graph Memory)

**File:** `docker-compose-falkordb.yml`

### Pre-deployment checklist:
- [ ] Verify `traefik-public` network name matches your setup
- [ ] (Optional) Set `FALKORDB_PASSWORD` for authentication
- [ ] Decide: Traefik TCP routing (complex) OR internal Docker network only (recommended)

### Deploy via Hostinger UI:
1. Create new project: **"memory-falkordb"**
2. Upload `docker-compose-falkordb.yml` as `docker-compose.yml`
3. Deploy

### Connect from OpenClaw container:

**Via Docker network (internal, recommended):**
```python
from graphiti_core import Graphiti
graphiti = Graphiti(redis_url="redis://memory-falkordb:6379")
```

**Note:** FalkorDB uses Redis protocol (TCP), not HTTP. Traefik HTTP routing won't work. For external access, you'd need to configure a Traefik TCP entrypoint (not recommended unless absolutely necessary).

---

## 3. Network Configuration

Both containers must join the **same Docker network** as your OpenClaw container for internal communication.

**Check your Traefik network name:**
```bash
docker network ls | grep traefik
```

If it's not `traefik-public`, update both compose files:
```yaml
networks:
  your-actual-network-name:
    external: true
```

---

## 4. Integration with OpenClaw

Once deployed, update Layer 0 agent or create integration scripts:

### Qdrant (Vector Search)
- Store conversation embeddings
- Semantic search across memory
- Recall by similarity

### FalkorDB (Graph Memory)
- Store relationships between entities
- Temporal reasoning
- Causal chains

### Example: Hybrid Memory Query
```python
# 1. Vector search for semantic recall
from qdrant_client import QdrantClient
client = QdrantClient(url="http://memory-qdrant:6333")
results = client.search(
    collection_name="conversations",
    query_vector=embedding,
    limit=5
)

# 2. Graph traversal for relational context
from graphiti_core import Graphiti
graphiti = Graphiti(redis_url="redis://memory-falkordb:6379")
graph_context = graphiti.search(query="What did we decide about X?")

# 3. Combine results for final answer
```

---

## 5. Resource Allocation

**Qdrant:**
- Recommended: 1 GB RAM minimum, 2 GB+ for production
- Storage: Scales with # of vectors (estimate ~1 KB per vector)

**FalkorDB:**
- Recommended: 512 MB RAM minimum, 1 GB+ for production
- Storage: Scales with graph size (nodes + edges)

**Total additional resource footprint:** ~2–3 GB RAM

Check your Hostinger VPS plan capacity before deploying.

---

## 6. Deployment Order

1. Deploy **memory-qdrant** first
2. Verify Qdrant dashboard accessible
3. Deploy **memory-falkordb**
4. Verify FalkorDB connectivity from OpenClaw container
5. Integrate into Layer 0 agent or create dedicated memory routing script

---

## 7. Troubleshooting

**Qdrant not accessible:**
- Check Traefik labels in compose file
- Verify DNS points to VPS IP
- Check Traefik logs for routing errors

**FalkorDB not accessible:**
- Ensure OpenClaw container is on same Docker network
- Test connection: `docker exec openclaw-container redis-cli -h memory-falkordb ping`
- Check FalkorDB logs: `docker logs memory-falkordb`

**Network issues:**
- Verify network name: `docker network inspect traefik-public`
- Ensure all containers connected: `docker network inspect traefik-public | grep Name`

---

## 8. Alternative: Neo4j Instead of FalkorDB

If you prefer HTTP API + native Traefik integration, consider Neo4j:

```yaml
services:
  neo4j:
    image: neo4j:latest
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt protocol
    environment:
      NEO4J_AUTH: neo4j/your-password
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.neo4j.rule=Host(`neo4j.yourdomain.com`)"
      - "traefik.http.services.neo4j.loadbalancer.server.port=7474"
```

Neo4j has better tooling (browser UI, cypher query language) but higher resource footprint.

---

## Next Steps

Once deployed:
1. Create Qdrant collection schema for conversation embeddings
2. Design FalkorDB graph schema (entity types, relationship types)
3. Integrate into Layer 0 agent memory routing logic
4. Test hybrid queries (vector + graph)
5. Monitor resource usage and adjust allocations

---

**Files:**
- `docker-compose-qdrant.yml` — Qdrant vector search service
- `docker-compose-falkordb.yml` — FalkorDB graph memory service
- This guide — Deployment instructions

**Status:** Ready for deployment. No code changes to OpenClaw container required.
