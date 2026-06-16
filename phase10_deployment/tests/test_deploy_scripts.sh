#!/usr/bin/env bash
# ==============================================================================
# Unit Tests for Phase 10 Deployment Scripts
# Uses BATS (Bash Automated Testing System).
#
# Install BATS:
#   brew install bats-core            # macOS
#   sudo apt-get install bats         # Debian / Ubuntu
#
# Run tests:
#   bats phase10_deployment/tests/test_deploy_scripts.sh
#
# Or run via the helper:
#   bash phase10_deployment/tests/test_deploy_scripts.sh
# ==============================================================================

# ── BATS bootstrap (auto-install if missing) ───────────────────────────────────
if ! command -v bats &>/dev/null; then
    echo "BATS not found. Running tests with a minimal pure-bash harness."
    BATS_FALLBACK=1
else
    BATS_FALLBACK=0
fi

# ── Test helpers & fixtures ────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TMP_DIR="$(mktemp -d)"

# Minimal .env fixture used by tests
make_env() {
    cat > "${TMP_DIR}/.env" <<EOF
DOMAIN_NAME=test.co2.local
CERTBOT_EMAIL=test@example.com
INFLUXDB_TOKEN=test-token-abc123
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_ORG=co2-org
INFLUXDB_BUCKET=co2-data
DOCKER_INFLUXDB_INIT_USERNAME=admin
DOCKER_INFLUXDB_INIT_PASSWORD=TestPass123!
DOCKER_INFLUXDB_INIT_ORG=co2-org
DOCKER_INFLUXDB_INIT_BUCKET=co2-data
MQTT_BROKER=mosquitto
MQTT_TOPIC=iot/co2/sensor1
SECRET_KEY=test-secret-key
DASHBOARD_SECRET_KEY=test-dashboard-key
IMAGE_TAG=v1.2.0
EOF
}

# ── Pure-bash fallback harness ─────────────────────────────────────────────────
if [[ "${BATS_FALLBACK}" == "1" ]]; then
    PASS_COUNT=0; FAIL_COUNT=0

    run_test() {
        local name="$1"; shift
        if "$@" &>/dev/null 2>&1; then
            printf '\033[32m  ✔ PASS\033[0m  %s\n' "${name}"; PASS_COUNT=$((PASS_COUNT+1))
        else
            printf '\033[31m  ✘ FAIL\033[0m  %s\n' "${name}"; FAIL_COUNT=$((FAIL_COUNT+1))
        fi
    }

    # ── Tests (bash harness) ──────────────────────────────────────────────────
    echo ""; echo "=== Phase 10 Deployment Script Tests ==="; echo ""

    # T01 – deploy.sh exists and is executable
    run_test "T01: deploy.sh is executable" \
        test -x "${DEPLOY_DIR}/scripts/deploy.sh"

    # T02 – rollback.sh exists and is executable
    run_test "T02: rollback.sh is executable" \
        test -x "${DEPLOY_DIR}/scripts/rollback.sh"

    # T03 – backup.sh exists and is executable
    run_test "T03: backup.sh is executable" \
        test -x "${DEPLOY_DIR}/scripts/backup.sh"

    # T04 – health_check.sh exists and is executable
    run_test "T04: health_check.sh is executable" \
        test -x "${DEPLOY_DIR}/scripts/health_check.sh"

    # T05 – generate_certs.sh exists and is executable
    run_test "T05: generate_certs.sh is executable" \
        test -x "${DEPLOY_DIR}/scripts/generate_certs.sh"

    # T06 – deploy.sh fails with no .env present
    run_test "T06: deploy.sh errors without .env" bash -c "
        cd '${TMP_DIR}'
        rm -f .env
        bash '${DEPLOY_DIR}/scripts/deploy.sh' 2>&1 | grep -q 'not found'
    "

    # T07 – rollback.sh fails with no .env present
    run_test "T07: rollback.sh errors without .env" bash -c "
        cd '${TMP_DIR}'
        rm -f .env
        bash '${DEPLOY_DIR}/scripts/rollback.sh' 2>&1 | grep -q 'not found'
    "

    # T08 – backup.sh fails with no .env present
    run_test "T08: backup.sh errors without .env" bash -c "
        cd '${TMP_DIR}'
        rm -f .env
        bash '${DEPLOY_DIR}/scripts/backup.sh' 2>&1 | grep -q 'not found'
    "

    # T09 – backup.sh fails when INFLUXDB_TOKEN is empty in .env
    run_test "T09: backup.sh errors when INFLUXDB_TOKEN missing" bash -c "
        cd '${TMP_DIR}'
        echo 'DOMAIN_NAME=test.co2.local' > .env
        bash '${DEPLOY_DIR}/scripts/backup.sh' 2>&1 | grep -q 'INFLUXDB_TOKEN'
    "

    # T10 – rollback.sh --list does not crash when no history exists
    run_test "T10: rollback.sh --list works with no history" bash -c "
        cd '${TMP_DIR}'
        make_env 2>/dev/null || true
        bash '${DEPLOY_DIR}/scripts/rollback.sh' --list 2>&1 | grep -q 'history\|Recent'
    "

    # T11 – generate_certs.sh reads DOMAIN_NAME from .env
    run_test "T11: generate_certs.sh picks DOMAIN_NAME from .env" bash -c "
        cd '${TMP_DIR}'
        make_env
        bash '${DEPLOY_DIR}/scripts/generate_certs.sh' 2>&1 | grep -q 'test.co2.local'
    "

    # T12 – generate_certs.sh skips if certs already exist
    run_test "T12: generate_certs.sh skips regeneration" bash -c "
        cd '${TMP_DIR}'
        make_env
        mkdir -p nginx/certs/live/test.co2.local
        touch nginx/certs/live/test.co2.local/privkey.pem
        touch nginx/certs/live/test.co2.local/fullchain.pem
        bash '${DEPLOY_DIR}/scripts/generate_certs.sh' 2>&1 | grep -q 'Skipping'
    "

    # T13 – docker-compose.yml YAML is syntactically valid
    run_test "T13: docker-compose.yml is valid YAML" bash -c "
        python3 -c \"import yaml; yaml.safe_load(open('${DEPLOY_DIR}/docker-compose.yml'))\"
    "

    # T14 – .env.prod.example contains all required keys
    run_test "T14: .env.prod.example has DOMAIN_NAME key" \
        grep -q "^DOMAIN_NAME=" "${DEPLOY_DIR}/.env.prod.example"

    run_test "T15: .env.prod.example has INFLUXDB_TOKEN key" \
        grep -q "^INFLUXDB_TOKEN=" "${DEPLOY_DIR}/.env.prod.example"

    run_test "T16: .env.prod.example has SECRET_KEY key" \
        grep -q "^SECRET_KEY=" "${DEPLOY_DIR}/.env.prod.example"

    run_test "T17: .env.prod.example has DASHBOARD_SECRET_KEY key" \
        grep -q "^DASHBOARD_SECRET_KEY=" "${DEPLOY_DIR}/.env.prod.example"

    # T18 – Kubernetes manifests exist
    run_test "T18: k8s/namespace.yaml exists" \
        test -f "${DEPLOY_DIR}/k8s/namespace.yaml"

    run_test "T19: k8s/configmap.yaml exists" \
        test -f "${DEPLOY_DIR}/k8s/configmap.yaml"

    run_test "T20: k8s/secrets.yaml exists" \
        test -f "${DEPLOY_DIR}/k8s/secrets.yaml"

    run_test "T21: k8s/influxdb.yaml exists" \
        test -f "${DEPLOY_DIR}/k8s/influxdb.yaml"

    run_test "T22: k8s/mosquitto.yaml exists" \
        test -f "${DEPLOY_DIR}/k8s/mosquitto.yaml"

    run_test "T23: k8s/backend.yaml exists" \
        test -f "${DEPLOY_DIR}/k8s/backend.yaml"

    run_test "T24: k8s/ingestion.yaml exists" \
        test -f "${DEPLOY_DIR}/k8s/ingestion.yaml"

    run_test "T25: k8s/dashboard.yaml exists" \
        test -f "${DEPLOY_DIR}/k8s/dashboard.yaml"

    run_test "T26: k8s/ingress.yaml exists" \
        test -f "${DEPLOY_DIR}/k8s/ingress.yaml"

    # T27 – Nginx config exists
    run_test "T27: nginx/nginx.conf exists" \
        test -f "${DEPLOY_DIR}/nginx/nginx.conf"

    run_test "T28: nginx/conf.d/co2-system.conf exists" \
        test -f "${DEPLOY_DIR}/nginx/conf.d/co2-system.conf"

    # T29 – Nginx conf has SSL/HTTPS block
    run_test "T29: Nginx conf includes ssl_certificate directive" \
        grep -q "ssl_certificate" "${DEPLOY_DIR}/nginx/conf.d/co2-system.conf"

    # T30 – Nginx conf has WebSocket upgrade headers
    run_test "T30: Nginx conf has WebSocket Upgrade header" \
        grep -q "Upgrade" "${DEPLOY_DIR}/nginx/conf.d/co2-system.conf"

    # ── Summary ───────────────────────────────────────────────────────────────
    echo ""
    echo "======================================================"
    printf "Results: \033[32m%d passed\033[0m, \033[31m%d failed\033[0m\n" \
        "${PASS_COUNT}" "${FAIL_COUNT}"
    echo "======================================================"
    rm -rf "${TMP_DIR}"
    [[ "${FAIL_COUNT}" -eq 0 ]]
    exit $?
fi

# ── BATS test definitions (only reached when bats is installed) ────────────────
setup() { make_env; cd "${TMP_DIR}"; }
teardown() { rm -rf "${TMP_DIR}"; }

@test "deploy.sh is executable" {
    [ -x "${DEPLOY_DIR}/scripts/deploy.sh" ]
}

@test "rollback.sh is executable" {
    [ -x "${DEPLOY_DIR}/scripts/rollback.sh" ]
}

@test "backup.sh is executable" {
    [ -x "${DEPLOY_DIR}/scripts/backup.sh" ]
}

@test "health_check.sh is executable" {
    [ -x "${DEPLOY_DIR}/scripts/health_check.sh" ]
}

@test "generate_certs.sh is executable" {
    [ -x "${DEPLOY_DIR}/scripts/generate_certs.sh" ]
}

@test "deploy.sh errors without .env" {
    rm -f .env
    run bash "${DEPLOY_DIR}/scripts/deploy.sh"
    [ "${status}" -ne 0 ]
    [[ "${output}" == *"not found"* ]]
}

@test "rollback.sh errors without .env" {
    rm -f .env
    run bash "${DEPLOY_DIR}/scripts/rollback.sh"
    [ "${status}" -ne 0 ]
}

@test "backup.sh errors without .env" {
    rm -f .env
    run bash "${DEPLOY_DIR}/scripts/backup.sh"
    [ "${status}" -ne 0 ]
}

@test "backup.sh errors when INFLUXDB_TOKEN missing" {
    echo "DOMAIN_NAME=test" > .env
    run bash "${DEPLOY_DIR}/scripts/backup.sh"
    [ "${status}" -ne 0 ]
    [[ "${output}" == *"INFLUXDB_TOKEN"* ]]
}

@test "rollback.sh --list works with no history" {
    run bash "${DEPLOY_DIR}/scripts/rollback.sh" --list
    [ "${status}" -eq 0 ]
}

@test "generate_certs.sh picks DOMAIN_NAME from .env" {
    run bash "${DEPLOY_DIR}/scripts/generate_certs.sh"
    [[ "${output}" == *"test.co2.local"* ]]
}

@test "generate_certs.sh skips regeneration if certs exist" {
    mkdir -p nginx/certs/live/test.co2.local
    touch nginx/certs/live/test.co2.local/{privkey.pem,fullchain.pem}
    run bash "${DEPLOY_DIR}/scripts/generate_certs.sh"
    [ "${status}" -eq 0 ]
    [[ "${output}" == *"Skipping"* ]]
}

@test "docker-compose.yml is valid YAML" {
    run python3 -c "import yaml; yaml.safe_load(open('${DEPLOY_DIR}/docker-compose.yml'))"
    [ "${status}" -eq 0 ]
}

@test ".env.prod.example has required keys" {
    grep -q "^DOMAIN_NAME=" "${DEPLOY_DIR}/.env.prod.example"
    grep -q "^INFLUXDB_TOKEN=" "${DEPLOY_DIR}/.env.prod.example"
    grep -q "^SECRET_KEY=" "${DEPLOY_DIR}/.env.prod.example"
    grep -q "^DASHBOARD_SECRET_KEY=" "${DEPLOY_DIR}/.env.prod.example"
}

@test "All k8s manifests exist" {
    for f in namespace configmap secrets influxdb mosquitto backend ingestion dashboard ingress; do
        [ -f "${DEPLOY_DIR}/k8s/${f}.yaml" ]
    done
}

@test "Nginx conf includes ssl_certificate" {
    grep -q "ssl_certificate" "${DEPLOY_DIR}/nginx/conf.d/co2-system.conf"
}

@test "Nginx conf includes WebSocket Upgrade headers" {
    grep -q "Upgrade" "${DEPLOY_DIR}/nginx/conf.d/co2-system.conf"
}
