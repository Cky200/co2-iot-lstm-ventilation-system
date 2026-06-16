#!/usr/bin/env bash
# ==============================================================================
# InfluxDB 2.x Database Backup Automation Script
# Performs live database backups, compresses target archives, and prunes
# historical backups older than the retention period (default: 30 days).
# ==============================================================================
set -euo pipefail

# Navigation to deployment directory root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${DEPLOY_DIR}"

# Backup directories configuration
BACKUP_PARENT_DIR="./backups"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
HOST_BACKUP_DIR="${BACKUP_PARENT_DIR}/influx_${TIMESTAMP}"
CONTAINER_TEMP_DIR="/tmp/influx_backup_temp"
RETENTION_DAYS=30

echo "=========================================================="
echo "Starting database backup at $(date)"
echo "=========================================================="

# 1. Safety Check: Validate Environment & Credentials
if [ ! -f .env ]; then
    echo "ERROR: Environment config '.env' file not found!"
    exit 1
fi

# Load token from .env file
TOKEN=$(grep -E "^INFLUXDB_TOKEN=" .env | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d '[:space:]') || true
if [ -z "${TOKEN}" ]; then
    echo "ERROR: INFLUXDB_TOKEN is not defined in .env file."
    exit 1
fi

CONTAINER_NAME="co2-influxdb-prod"
# Verify if InfluxDB container is running
if ! docker ps --filter "name=${CONTAINER_NAME}" --filter "status=running" | grep -q "${CONTAINER_NAME}"; then
    echo "ERROR: Container '${CONTAINER_NAME}' is not running."
    exit 1
fi

# 2. Initialize directories
mkdir -p "${BACKUP_PARENT_DIR}"

# Clean up any residual temp directories inside container from previous runs
docker exec "${CONTAINER_NAME}" rm -rf "${CONTAINER_TEMP_DIR}"

# 3. Execute backup inside the container using influx CLI tools
echo "--> Generating database snapshot inside container..."
docker exec "${CONTAINER_NAME}" influx backup "${CONTAINER_TEMP_DIR}" -t "${TOKEN}"

# 4. Copy generated backup files to the host
echo "--> Copying backup files to host path: ${HOST_BACKUP_DIR}..."
docker cp "${CONTAINER_NAME}:${CONTAINER_TEMP_DIR}" "${HOST_BACKUP_DIR}"

# 5. Clean up temporary files inside container
echo "--> Cleaning up temp files inside container..."
docker exec "${CONTAINER_NAME}" rm -rf "${CONTAINER_TEMP_DIR}"

# 6. Compress host backup files
echo "--> Compressing backup files..."
tar -czf "${HOST_BACKUP_DIR}.tar.gz" -C "${BACKUP_PARENT_DIR}" "influx_${TIMESTAMP}"
rm -rf "${HOST_BACKUP_DIR}"

echo "--> Backup file generated: ${HOST_BACKUP_DIR}.tar.gz"

# 7. Retention Policy: Prune backups older than 30 days
echo "--> Applying retention policy (Pruning backups older than ${RETENTION_DAYS} days)..."
find "${BACKUP_PARENT_DIR}" -name "influx_*.tar.gz" -type f -mtime +"${RETENTION_DAYS}" -exec rm -v {} \;

echo "=========================================================="
echo "Database backup completed successfully!"
echo "=========================================================="
