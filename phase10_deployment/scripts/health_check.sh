#!/usr/bin/env bash
# ==============================================================================
# Service Health Check Script
# Validates all container health states and probes every HTTP/TCP endpoint
# of the CO₂ IoT Ventilation System. Exits 1 if any check fails.
#
# Usage:
#   ./scripts/health_check.sh              # Check against localhost
#   ./scripts/health_check.sh <domain>    # Check against a named host
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${DEPLOY_DIR}"

HOST="${1:-localhost}"

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
PASS() { printf "  ${GREEN}✔ PASS${NC} — %s\n" "$*"; }
FAIL() { printf "  ${RED}✘ FAIL${NC} — %s\n" "$*"; FAILURES=$((FAILURES + 1)); }
INFO() { printf "  ${YELLOW}ℹ INFO${NC} — %s\n" "$*"; }
sep()  { echo "=========================================================="; }

FAILURES=0

sep
echo "CO₂ IoT System — Health Check Report"
echo "Host: ${HOST}  |  $(date '+%Y-%m-%d %H:%M:%S')"
sep

# ── 1. Docker container status ────────────────────────────────────────────────
echo ""
echo "[ 1/5 ] Container Status"
echo "------------------------------------------------------------"

check_container() {
    local name="$1"
    local status
    status=$(docker inspect --format='{{.State.Status}}' "${name}" 2>/dev/null || echo "missing")
    local health
    health=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}N/A{{end}}' "${name}" 2>/dev/null || echo "missing")
    if [[ "${status}" == "running" ]]; then
        PASS "${name}: running (health: ${health})"
    else
        FAIL "${name}: ${status} (health: ${health})"
    fi
}

check_container "co2-nginx-proxy"
check_container "co2-mqtt-broker-prod"
check_container "co2-influxdb-prod"
check_container "co2-backend-api-prod"
check_container "co2-ingestion-service-prod"
check_container "co2-dashboard-ui-prod"

# ── 2. HTTP Endpoint probes ───────────────────────────────────────────────────
echo ""
echo "[ 2/5 ] HTTP Endpoint Probes"
echo "------------------------------------------------------------"

probe_http() {
    local label="$1"
    local url="$2"
    local expected_status="${3:-200}"
    local actual_status
    actual_status=$(curl -sSo /dev/null -w "%{http_code}" --max-time 5 \
        --resolve "${HOST}:80:127.0.0.1" \
        --resolve "${HOST}:443:127.0.0.1" \
        -k "${url}" 2>/dev/null || echo "000")
    if [[ "${actual_status}" == "${expected_status}" ]]; then
        PASS "${label} → HTTP ${actual_status}"
    else
        FAIL "${label} → Expected HTTP ${expected_status}, got ${actual_status} (url: ${url})"
    fi
}

probe_http "Dashboard UI root"           "http://${HOST}/"          "301"  # HTTP→HTTPS redirect
probe_http "Dashboard /health"           "https://${HOST}/health"   "200"
probe_http "API root"                    "https://${HOST}/"         "200"
probe_http "FastAPI /api/v1/co2/history" "https://${HOST}/api/v1/co2/history" "401"   # Auth required = service up
probe_http "FastAPI /docs"               "https://${HOST}/docs"     "200"

# ── 3. TCP port reachability ──────────────────────────────────────────────────
echo ""
echo "[ 3/5 ] TCP Port Checks"
echo "------------------------------------------------------------"

probe_tcp() {
    local label="$1"
    local host="$2"
    local port="$3"
    if timeout 3 bash -c "echo >/dev/tcp/${host}/${port}" 2>/dev/null; then
        PASS "${label} (${host}:${port}) reachable"
    else
        FAIL "${label} (${host}:${port}) not reachable"
    fi
}

probe_tcp "Nginx HTTP"           "${HOST}" 80
probe_tcp "Nginx HTTPS"          "${HOST}" 443
probe_tcp "MQTT Broker"          "${HOST}" 1883

# ── 4. InfluxDB internal health ───────────────────────────────────────────────
echo ""
echo "[ 4/5 ] InfluxDB Internal Health"
echo "------------------------------------------------------------"

INFLUX_HEALTH=$(docker exec co2-influxdb-prod curl -sSo /dev/null -w "%{http_code}" \
    http://localhost:8086/health 2>/dev/null || echo "000")
if [[ "${INFLUX_HEALTH}" == "200" ]]; then
    PASS "InfluxDB /health → HTTP 200"
else
    FAIL "InfluxDB /health → got HTTP ${INFLUX_HEALTH}"
fi

# ── 5. SSL certificate expiry ─────────────────────────────────────────────────
echo ""
echo "[ 5/5 ] SSL Certificate Expiry"
echo "------------------------------------------------------------"

EXPIRY=$(echo | openssl s_client -connect "${HOST}:443" -servername "${HOST}" 2>/dev/null \
    | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2 || echo "")

if [[ -n "${EXPIRY}" ]]; then
    EXPIRY_EPOCH=$(date -d "${EXPIRY}" +%s 2>/dev/null || date -jf "%b %d %T %Y %Z" "${EXPIRY}" +%s 2>/dev/null || echo "0")
    NOW_EPOCH=$(date +%s)
    DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

    if (( DAYS_LEFT > 14 )); then
        PASS "SSL certificate valid — expires ${EXPIRY} (${DAYS_LEFT} days remaining)"
    elif (( DAYS_LEFT > 0 )); then
        INFO "SSL certificate expiring SOON — ${DAYS_LEFT} days left (${EXPIRY})"
        FAILURES=$((FAILURES + 1))
    else
        FAIL "SSL certificate has EXPIRED (${EXPIRY})"
    fi
else
    INFO "SSL check skipped (could not connect to ${HOST}:443 — may be self-signed or host offline)"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
sep
echo ""
if (( FAILURES == 0 )); then
    printf "${GREEN}All health checks passed.${NC}\n"
    exit 0
else
    printf "${RED}${FAILURES} check(s) failed. Review output above.${NC}\n"
    exit 1
fi
