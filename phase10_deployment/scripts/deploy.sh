#!/usr/bin/env bash
# ==============================================================================
# Automated Production Deployment Script
# Validates the system environment, pulls images, compiles dependencies,
# and spins up container services smoothly with minimal downtime.
# ==============================================================================
set -euo pipefail

# Navigation to deployment directory root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${DEPLOY_DIR}"

echo "=========================================================="
echo "Initializing Hybrid IoT-LSTM Ventilation System Deploy"
echo "=========================================================="

# 1. Safety Check: Validate Environment File
if [ ! -f .env ]; then
    echo "ERROR: Production environment file '.env' not found!"
    echo "Please copy '.env.prod.example' to '.env' and configure it first:"
    echo "  cp .env.prod.example .env"
    exit 1
fi

# 2. Check for required Docker CLI tools
if ! command -v docker &> /dev/null; then
    echo "ERROR: docker CLI tool not found. Docker must be installed to deploy."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "ERROR: docker compose command not found. Docker Compose V2 is required."
    exit 1
fi

# 3. Pull latest images from the package registry
echo "--> Pulling latest container images..."
docker compose pull

# 4. Build any images with local build fallback overrides
echo "--> Rebuilding local custom images (if overridden)..."
docker compose build --pull

# 5. Bring services up in daemon (background) mode
echo "--> Starting production containers..."
docker compose up -d --remove-orphans

# 6. Post-Deployment validation check
echo "--> Verifying service health..."
sleep 5 # Allow time for initial container boot sequences

docker compose ps

echo "=========================================================="
echo "Deployment sequence completed successfully!"
echo "Verify dashboard is accessible at your configured DOMAIN_NAME."
echo "Use 'docker compose logs -f' to trace live logs."
echo "=========================================================="
