#!/usr/bin/env bash
# ==============================================================================
# Self-Signed SSL Certificate Generator Script
# Generates dummy/self-signed certificates for development or staging validation
# to allow Nginx to start up successfully before running Certbot.
# ==============================================================================
set -euo pipefail

# Navigation to deployment directory root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${DEPLOY_DIR}"

# 1. Load domain configuration from .env if present
DOMAIN="co2.example.com"
if [ -f .env ]; then
    # Load domain from env, strip quotes and whitespace
    ENV_DOMAIN=$(grep -E "^DOMAIN_NAME=" .env | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d '[:space:]') || true
    if [ -n "${ENV_DOMAIN}" ]; then
        DOMAIN="${ENV_DOMAIN}"
    fi
fi

echo "=========================================================="
echo "Generating self-signed SSL certificates for: ${DOMAIN}"
echo "=========================================================="

# Create paths inside local Nginx mount directory to store local self-signed certs
CERT_DIR="nginx/certs/live/${DOMAIN}"
mkdir -p "${CERT_DIR}"

# 2. Check if OpenSSL is installed
if ! command -v openssl &> /dev/null; then
    echo "ERROR: openssl command not found. Please install openssl first."
    exit 1
fi

# 3. Generate private key and certificate chain (valid for 365 days)
PRIVATE_KEY="${CERT_DIR}/privkey.pem"
FULL_CHAIN="${CERT_DIR}/fullchain.pem"

if [ -f "${PRIVATE_KEY}" ] && [ -f "${FULL_CHAIN}" ]; then
    echo "Certificates already exist under ${CERT_DIR}."
    echo "Skipping generation. Delete files to regenerate."
    exit 0
fi

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "${PRIVATE_KEY}" \
    -out "${FULL_CHAIN}" \
    -subj "/CN=${DOMAIN}/O=CO2 IoT Ventilation System/OU=Deployment"

echo "=========================================================="
echo "Certificates generated successfully!"
echo "Location: ${CERT_DIR}"
echo ""
echo "Note: Update your docker-compose.yml configuration to map"
echo "this local folder for self-signed staging: "
echo "  - ./nginx/certs:/etc/letsencrypt"
echo "=========================================================="
