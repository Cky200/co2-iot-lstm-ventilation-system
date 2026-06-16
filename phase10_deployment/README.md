# Phase 10: Production Deployment

Complete deployment guide for the **Hybrid IoT–LSTM CO₂ Monitoring and Automated Ventilation Control System**. This covers Docker Compose, Kubernetes, SSL/TLS, reverse proxy, environment configuration, health checking, rollback, backup, and ongoing maintenance.

---

## Architecture Overview

```
┌─────────────────────── EXTERNAL TRAFFIC ──────────────────────────┐
│  Client Browser   IoT Sensor (Raspberry Pi)    Admin SSH Tunnel   │
│       │                    │ MQTT:1883                │           │
└───────┼────────────────────┼──────────────────────────┼───────────┘
        │ HTTPS:443          │                          │
        ▼                    ▼                          │
 ┌─────────────┐      ┌──────────────┐                  │
 │  Nginx / K8s│      │  Mosquitto   │◄─ IoT devices    │
 │  Ingress    │      │  MQTT Broker │                  │
 └──────┬──────┘      └──────┬───────┘                  │
        │                    │ subscribe                │
   ┌────┴──────────┐   ┌─────▼───────┐          ┌──────▼─────────┐
   │  Dashboard UI │   │  Ingestion  │           │   InfluxDB UI  │
   │  Flask :5007  │   │  Daemon     │─────────► │   (via tunnel) │
   └───────────────┘   └─────────────┘           └────────────────┘
   ┌───────────────┐   ┌─────────────────────────────────────────┐
   │  FastAPI      │   │           InfluxDB :8086                │
   │  Backend :8000│──►│  (internal only, not exposed to host)   │
   └───────────────┘   └─────────────────────────────────────────┘
```

---

## Deployment Modes

| Mode | Stack | Best For |
|------|-------|----------|
| **Docker Compose** | `docker-compose.yml` | Single VM / VPS |
| **Kubernetes** | `k8s/*.yaml` | Managed clusters (EKS/GKE/AKS) |

---

## Docker Compose Deployment (Single Server)

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Docker Engine | 24+ |
| Docker Compose V2 | 2.20+ |
| OpenSSL | 3.x |
| A registered domain pointed at your server | – |

### Step 1 — Clone & Configure

```bash
git clone https://github.com/Cky200/co2-iot-lstm-ventilation-system.git
cd co2-iot-lstm-ventilation-system/phase10_deployment

# Copy and fill in your production secrets
cp .env.prod.example .env
nano .env          # or: vim .env / code .env
```

**Required values to change in `.env`:**

| Variable | What to set |
|----------|-------------|
| `DOMAIN_NAME` | Your FQDN, e.g. `co2.yourdomain.com` |
| `CERTBOT_EMAIL` | Your email for Let's Encrypt alerts |
| `DOCKER_INFLUXDB_INIT_PASSWORD` | Strong unique DB password |
| `INFLUXDB_TOKEN` | `openssl rand -hex 32` |
| `SECRET_KEY` | `openssl rand -hex 32` |
| `DASHBOARD_SECRET_KEY` | `openssl rand -hex 32` |

---

### Step 2 — SSL / HTTPS Setup

Nginx requires certificates to start. Pick one path:

#### Path A — Live Production (Let's Encrypt)

Solve the chicken-and-egg problem: generate placeholder certs first so Nginx can start, then swap them with real Let's Encrypt certificates.

```bash
# 1. Generate placeholder self-signed cert (lets Nginx start)
./scripts/generate_certs.sh

# 2. Start only the infrastructure layer (Nginx + databases + MQTT)
docker compose up -d nginx influxdb mosquitto certbot

# 3. Obtain real Let's Encrypt certificate via HTTP-01 challenge
source .env
docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d "${DOMAIN_NAME}" \
  --email "${CERTBOT_EMAIL}" \
  --agree-tos --no-eff-email --force-renewal

# 4. Reload Nginx to pick up the new certificate
docker compose exec nginx nginx -s reload
```

Automatic renewal: Certbot runs inside its container and polls every 12 h. No cron job required.

#### Path B — Staging / Offline Testing (Self-Signed)

```bash
./scripts/generate_certs.sh

# Mount generated certs instead of the named volume
# Edit docker-compose.yml: change  certbot_certs:/etc/letsencrypt:ro
#                              to  ./nginx/certs:/etc/letsencrypt:ro
```

---

### Step 3 — Launch the Full Stack

```bash
./scripts/deploy.sh
```

The deploy script:
1. Validates `.env` and Docker CLI presence.
2. Pulls latest images from GHCR.
3. Builds any services not pulled (local fallback).
4. Starts all containers with `docker compose up -d --remove-orphans`.
5. Reports container states.

Verify all services are healthy:

```bash
./scripts/health_check.sh            # checks localhost
./scripts/health_check.sh co2.yourdomain.com   # checks remote domain
```

---

### Step 4 — Verify Endpoints

| URL | Expected |
|-----|----------|
| `http://co2.yourdomain.com/` | 301 → HTTPS |
| `https://co2.yourdomain.com/` | Dashboard UI |
| `https://co2.yourdomain.com/health` | `{"status":"ok"}` |
| `https://co2.yourdomain.com/api/v1/co2/history` | 401 Unauthorized (auth required = API up) |
| `https://co2.yourdomain.com/docs` | FastAPI Swagger UI |

---

## Kubernetes Deployment (Managed Cluster)

### Prerequisites

```bash
# Helm 3
brew install helm          # macOS
# kubectl connected to your cluster
kubectl cluster-info

# Install ingress-nginx controller
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx \
  --namespace ingress-nginx --create-namespace

# Install cert-manager (handles Let's Encrypt automatically)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
```

### Apply Manifests in Order

```bash
K8S_DIR=phase10_deployment/k8s

# 1. Namespace first
kubectl apply -f "${K8S_DIR}/namespace.yaml"

# 2. Encode and apply secrets (edit secrets.yaml values first!)
#    Encode: echo -n 'your-value' | base64
kubectl apply -f "${K8S_DIR}/secrets.yaml"

# 3. ConfigMap
kubectl apply -f "${K8S_DIR}/configmap.yaml"

# 4. Databases and broker (stateful — apply before apps)
kubectl apply -f "${K8S_DIR}/influxdb.yaml"
kubectl apply -f "${K8S_DIR}/mosquitto.yaml"

# 5. Application workloads
kubectl apply -f "${K8S_DIR}/backend.yaml"
kubectl apply -f "${K8S_DIR}/ingestion.yaml"
kubectl apply -f "${K8S_DIR}/dashboard.yaml"

# 6. Ingress (triggers cert-manager to issue TLS certificate)
#    Edit ingress.yaml: replace co2.example.com and admin@example.com first
kubectl apply -f "${K8S_DIR}/ingress.yaml"
```

### Verify K8s Deployment

```bash
# All pods running?
kubectl get pods -n co2-system

# Certificate issued?
kubectl get certificate -n co2-system

# Ingress assigned an external IP?
kubectl get ingress -n co2-system
```

---

## IoT Device Configuration

For Raspberry Pi sensors (Phase 5 firmware) to publish data to the production server, set the broker host in the firmware config:

```python
# phase5_iot_firmware/iot_firmware/config.py
MQTT_BROKER = "co2.yourdomain.com"   # Your production domain
MQTT_PORT   = 1883
```

Ensure port `1883` is open in your server firewall / cloud security group:

```bash
# UFW (Ubuntu)
sudo ufw allow 1883/tcp comment "MQTT broker"

# iptables
sudo iptables -A INPUT -p tcp --dport 1883 -j ACCEPT
```

---

## Maintenance Operations

### Rollback to a Previous Version

```bash
# Roll back to a specific image tag
./scripts/rollback.sh v1.3.1

# Or roll back to the automatically recorded previous tag
./scripts/rollback.sh

# List recent rollback history
./scripts/rollback.sh --list
```

The rollback script patches `IMAGE_TAG` in `.env`, pulls the target image from GHCR, recreates the affected containers, and runs a health gate before confirming success.

### Database Backup

```bash
# One-shot backup (gzipped snapshot in ./backups/)
./scripts/backup.sh

# Schedule daily 2 AM backups
crontab -e
# Add:
0 2 * * * /bin/bash /path/to/phase10_deployment/scripts/backup.sh >> /var/log/co2_backup.log 2>&1
```

Backups older than 30 days are automatically pruned.

### Access InfluxDB UI Securely

InfluxDB is not exposed on any public port. SSH-tunnel to the server:

```bash
ssh -L 8086:localhost:8086 user@co2.yourdomain.com
# Then open: http://localhost:8086
```

### View Live Logs

```bash
docker compose logs -f co2-backend      # FastAPI logs
docker compose logs -f co2-dashboard    # Dashboard logs
docker compose logs -f co2-ingestion    # MQTT ingestion logs
docker compose logs -f nginx            # Nginx access/error logs
```

---

## Running the Deployment Tests

A 30-test suite validates scripts and configs without requiring a live Docker environment:

```bash
# With BATS installed (recommended)
bats phase10_deployment/tests/test_deploy_scripts.sh

# Without BATS (pure-bash fallback)
bash phase10_deployment/tests/test_deploy_scripts.sh
```

Install BATS:
```bash
brew install bats-core    # macOS
sudo apt-get install bats # Debian/Ubuntu
```

---

## Security Checklist

- [ ] All secret values in `.env` changed from template defaults
- [ ] `.env` added to `.gitignore` (never committed)
- [ ] InfluxDB port 8086 **not** exposed in `docker-compose.yml` (internal only)
- [ ] `SECRET_KEY` and `DASHBOARD_SECRET_KEY` generated with `openssl rand -hex 32`
- [ ] HSTS header enabled in Nginx (`Strict-Transport-Security`)
- [ ] SSL session tickets disabled in Nginx (`ssl_session_tickets off`)
- [ ] Certbot auto-renewal container running
- [ ] SSH key-based access only (password auth disabled on server)
- [ ] Firewall: only ports 80, 443, 1883, 22 open to external traffic
