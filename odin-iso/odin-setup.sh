#!/bin/bash
# =============================================================================
# ODIN-CLAW: Post-Install Setup Script
# Run this after Linux Mint is installed and you're logged in as boss
# Usage: bash odin-setup.sh
# =============================================================================

set -e

ODIN_DIR="/home/boss/odin"
LOG="/home/boss/odin-setup.log"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"
}

echo "============================================"
echo "  ODIN-CLAW SETUP - $(date)"
echo "============================================"

# --- Step 1: System Update ---
log "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# --- Step 2: Install Dependencies ---
log "Installing dependencies..."
sudo apt install -y \
    curl git nano htop ufw \
    ca-certificates gnupg \
    lsb-release apt-transport-https

# --- Step 3: Install Docker ---
log "Installing Docker..."
curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
sudo sh /tmp/get-docker.sh
sudo usermod -aG docker boss
sudo systemctl enable docker
sudo systemctl start docker
log "Docker installed."

# --- Step 4: Install Docker Compose plugin ---
log "Installing Docker Compose..."
sudo apt install -y docker-compose-plugin
docker compose version
log "Docker Compose installed."

# --- Step 5: Create Odin directory structure ---
log "Creating Odin directories..."
mkdir -p "$ODIN_DIR"/{workspace,qdrant,falkordb,ollama,jupyter}
log "Directories created at $ODIN_DIR"

# --- Step 6: Copy docker-compose.yml from USB (if present) ---
COMPOSE_SRC=""
for dev in /media/boss/*/docker-compose.yml; do
    if [ -f "$dev" ]; then
        COMPOSE_SRC="$dev"
        break
    fi
done

if [ -n "$COMPOSE_SRC" ]; then
    log "Found docker-compose.yml on USB at $COMPOSE_SRC"
    cp "$COMPOSE_SRC" "$ODIN_DIR/docker-compose.yml"
    log "Copied docker-compose.yml to $ODIN_DIR"
else
    log "No USB compose file found — writing embedded copy..."
    cat > "$ODIN_DIR/docker-compose.yml" << 'COMPOSE_EOF'
version: '3.8'

services:
  openclaw:
    image: openclaw/openclaw:latest
    container_name: openclaw-odin
    ports:
      - "3000:3000"
      - "8080:8080"
    volumes:
      - /home/boss/odin/workspace:/data/.openclaw/workspace
    environment:
      - NODE_ENV=production
    restart: unless-stopped
    networks:
      - odin-network

  ollama:
    image: ollama/ollama:latest
    container_name: ollama-odin
    ports:
      - "11434:11434"
    volumes:
      - /home/boss/odin/ollama:/root/.ollama
    restart: unless-stopped
    networks:
      - odin-network

  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-odin
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - /home/boss/odin/qdrant:/qdrant/storage
    restart: unless-stopped
    networks:
      - odin-network

  falkordb:
    image: falkordb/falkordb:latest
    container_name: falkordb-odin
    ports:
      - "6379:6379"
    volumes:
      - /home/boss/odin/falkordb:/data
    restart: unless-stopped
    networks:
      - odin-network

  jupyter:
    image: jupyter/base-notebook:latest
    container_name: jupyter-odin
    ports:
      - "8888:8888"
    volumes:
      - /home/boss/odin/workspace:/home/jovyan/work
    environment:
      - JUPYTER_ENABLE_LAB=yes
      - JUPYTER_TOKEN=odin-jupyter-2026
    restart: unless-stopped
    networks:
      - odin-network

networks:
  odin-network:
    driver: bridge
COMPOSE_EOF
fi

# --- Step 7: Firewall ---
log "Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 3000/tcp   # OpenClaw
sudo ufw allow 8080/tcp   # OpenClaw alt
sudo ufw allow 11434/tcp  # Ollama
sudo ufw allow 6333/tcp   # Qdrant
sudo ufw allow 8888/tcp   # Jupyter
sudo ufw --force enable
log "Firewall configured."

# --- Step 8: SSH Key Setup ---
log "Setting up SSH..."
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cat >> ~/.ssh/authorized_keys << 'SSH_EOF'
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPUmX8pYJe+3/SbHyXJFxYoakv+fCZ0B4VF2WIhk9CuO odin-claw
SSH_EOF
chmod 600 ~/.ssh/authorized_keys
log "SSH key installed."

# --- Step 9: Pull Docker images ---
log "Pulling Docker images (this will take 15-40 minutes)..."
cd "$ODIN_DIR"
sudo docker compose pull
log "All images pulled."

# --- Step 10: Start the stack ---
log "Starting Odin stack..."
sudo docker compose up -d
sleep 5
sudo docker compose ps
log "Odin stack is live."

# --- Done ---
echo ""
echo "============================================"
echo "  ODIN-CLAW IS ALIVE"
echo "  OpenClaw  → http://localhost:3000"
echo "  Ollama    → http://localhost:11434"
echo "  Qdrant    → http://localhost:6333"
echo "  Jupyter   → http://localhost:8888"
echo "  Token: odin-jupyter-2026"
echo "============================================"
echo ""
log "Setup complete. Full log at $LOG"
