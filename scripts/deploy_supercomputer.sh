#!/usr/bin/env bash
# ==============================================================================
# Nirma University Supercomputer Remote SSH Deployment Runbook & Automation Script
#
# This script automates production deployment on Nirma University's HPC Supercomputer node
# over SSH. It performs code update, Docker stack building, GPU verification, database
# migrations, seed initialization, model pulling, and endpoint health validation.
#
# Usage:
#   bash scripts/deploy_supercomputer.sh
# ==============================================================================

set -euo pipefail

RED='\030[0;31m'
GREEN='\030[0;32m'
YELLOW='\030[1;33m'
BLUE='\030[0;34m'
NC='\030[0m' # No Color

echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}  Nirma AI Call Agent — HPC Supercomputer Remote SSH Deployment   ${NC}"
echo -e "${BLUE}=====================================================================${NC}"

# 1. Verify environment configuration
if [ ! -f ".env" ]; then
    echo -e "${RED}[ERROR] Production .env file missing in repository root.${NC}"
    echo -e "${YELLOW}Please create .env using .env.example prior to running deployment.${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] Production .env file detected.${NC}"

# 2. Check NVIDIA GPU visibility on Supercomputer host
echo -e "${YELLOW}[STEP 1/6] Verifying NVIDIA GPU hardware passthrough...${NC}"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader || true
    echo -e "${GREEN}[OK] NVIDIA GPU hardware recognized.${NC}"
else
    echo -e "${YELLOW}[WARNING] nvidia-smi CLI not found in PATH. Proceeding with CPU/Fallback mode.${NC}"
fi

# 3. Pull latest git changes
echo -e "${YELLOW}[STEP 2/6] Pulling latest repository commits...${NC}"
git pull origin main || echo -e "${YELLOW}[NOTE] Local working copy up to date or git pull skipped.${NC}"

# 4. Build and launch Docker Compose stack
echo -e "${YELLOW}[STEP 3/6] Building container images & bringing up Docker stack...${NC}"
docker compose build
docker compose up -d

# 5. Execute Alembic schema migrations & seed default data
echo -e "${YELLOW}[STEP 4/6] Running PostgreSQL database migrations & seeding default data...${NC}"
# Wait for postgres container to be ready
until docker compose exec -T postgres pg_isready -U postgres -d ai_calls &> /dev/null; do
    echo -e "Waiting for PostgreSQL database container..."
    sleep 2
done

docker compose exec -T backend alembic upgrade head
docker compose exec -T backend python -m backend.seeds

# 6. Pull local LLM model weights into Ollama container
echo -e "${YELLOW}[STEP 5/6] Pulling Qwen-14B LLM quantized model checkpoint into Ollama...${NC}"
docker compose exec -T ollama ollama pull qwen:14b || echo -e "${YELLOW}[NOTE] Ollama model download deferred or model already cached.${NC}"

# 7. Validate system health probe
echo -e "${YELLOW}[STEP 6/6] Performing final endpoint health check...${NC}"
sleep 5
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health || echo "FAILED")

if [[ "$HEALTH_RESPONSE" == *"online"* ]]; then
    echo -e "${GREEN}=====================================================================${NC}"
    echo -e "${GREEN}  SUCCESS: Nirma AI Call Agent stack deployed successfully on HPC!   ${NC}"
    echo -e "${GREEN}  Health Status: $HEALTH_RESPONSE                                    ${NC}"
    echo -e "${GREEN}=====================================================================${NC}"
else
    echo -e "${RED}[ERROR] Health check probe failed. Server response: $HEALTH_RESPONSE${NC}"
    echo -e "${RED}Inspect container logs via: docker compose logs -f backend${NC}"
    exit 1
fi
