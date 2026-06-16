#!/usr/bin/env bash
# ==============================================================================
# Production Rollback Script
# Rolls the stack back to a previously tagged image version stored in GHCR.
# Usage:
#   ./scripts/rollback.sh                     # Rolls back to the previous tag
#   ./scripts/rollback.sh <tag>               # Rolls back to a specific tag
#   ./scripts/rollback.sh --list              # Lists the last 10 deployed tags
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${DEPLOY_DIR}"

ROLLBACK_TAG="${1:-}"
ROLLBACK_RECORD=".rollback_history"

# ── Helpers ──────────────────────────────────────────────────────────────────
log()  { echo "[$(date '+%H:%M:%S')] $*"; }
err()  { echo "[ERROR] $*" >&2; exit 1; }
sep()  { echo "=========================================================="; }

# ── Guards ────────────────────────────────────────────────────────────────────
[[ -f .env ]] || err "'.env' not found. Copy .env.prod.example to .env first."
command -v docker &>/dev/null || err "Docker CLI not found."
docker compose version &>/dev/null || err "Docker Compose V2 not found."

# ── List mode ─────────────────────────────────────────────────────────────────
if [[ "${ROLLBACK_TAG}" == "--list" ]]; then
    log "Recent rollback history (newest first):"
    if [[ -f "${ROLLBACK_RECORD}" ]]; then
        tail -r "${ROLLBACK_RECORD}" 2>/dev/null || tac "${ROLLBACK_RECORD}" | head -n 10
    else
        log "No rollback history recorded yet."
    fi
    exit 0
fi

# ── Determine target tag ───────────────────────────────────────────────────────
# If no tag supplied, derive the PREVIOUS tag from the rollback history file
if [[ -z "${ROLLBACK_TAG}" ]]; then
    if [[ ! -f "${ROLLBACK_RECORD}" ]] || [[ $(wc -l < "${ROLLBACK_RECORD}") -lt 2 ]]; then
        err "No previous tag found in rollback history. Provide a tag explicitly: ./rollback.sh <tag>"
    fi
    # Second-to-last line = the tag before the current one
    ROLLBACK_TAG=$(tail -2 "${ROLLBACK_RECORD}" | head -1 | awk '{print $1}')
    log "Auto-detected previous tag: ${ROLLBACK_TAG}"
fi

sep
log "CO₂ IoT System — Rollback to tag: ${ROLLBACK_TAG}"
sep

# ── Snapshot current state ────────────────────────────────────────────────────
CURRENT_TAG=$(grep -E "^IMAGE_TAG=" .env | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d '[:space:]') || true
CURRENT_TAG="${CURRENT_TAG:-latest}"
log "Current running tag: ${CURRENT_TAG}"
log "Target rollback tag: ${ROLLBACK_TAG}"

# ── Confirm ───────────────────────────────────────────────────────────────────
if [[ -t 0 ]]; then
    read -rp "Proceed with rollback? (yes/no) " CONFIRM
    [[ "${CONFIRM}" == "yes" ]] || { log "Rollback cancelled."; exit 0; }
fi

# ── Patch IMAGE_TAG in .env ───────────────────────────────────────────────────
log "Updating IMAGE_TAG in .env to ${ROLLBACK_TAG}..."
# In-place replace (portable sed for macOS & Linux)
if grep -qE "^IMAGE_TAG=" .env; then
    sed -i.bak "s|^IMAGE_TAG=.*|IMAGE_TAG=${ROLLBACK_TAG}|" .env
else
    echo "IMAGE_TAG=${ROLLBACK_TAG}" >> .env
fi

# ── Pull rollback images ───────────────────────────────────────────────────────
log "Pulling rollback images from registry..."
docker compose pull co2-backend co2-dashboard || true   # graceful — may be local build

# ── Replace running containers ────────────────────────────────────────────────
log "Recreating containers with rollback images..."
docker compose up -d --no-build --remove-orphans co2-backend co2-ingestion co2-dashboard

# ── Health gate (30-second window) ────────────────────────────────────────────
log "Waiting 15 s for containers to stabilise..."
sleep 15

UNHEALTHY=$(docker compose ps --filter "health=unhealthy" --format "{{.Name}}" 2>/dev/null || true)
if [[ -n "${UNHEALTHY}" ]]; then
    err "Rollback failed — unhealthy containers: ${UNHEALTHY}"
fi

# ── Record rollback event ─────────────────────────────────────────────────────
echo "${ROLLBACK_TAG}  $(date '+%Y-%m-%dT%H:%M:%S')  rolled-back-from:${CURRENT_TAG}" >> "${ROLLBACK_RECORD}"

sep
log "Rollback to ${ROLLBACK_TAG} completed successfully."
log "Run './scripts/health_check.sh' to verify all endpoints."
sep
