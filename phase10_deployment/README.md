# Phase 10: Production Deployment

This folder contains the production-grade configurations, gateway routing, certificate setups, and automation scripts for deploying the **Hybrid IoT–LSTM CO₂ Monitoring and Automated Ventilation Control System**.

---

## Deployment Architecture

The production environment orchestrates services in an isolated Docker network:

```
                  [ Inbound HTTP/HTTPS Traffic ]
                               │ (Port 80 / 443)
                               ▼
                       ┌───────────────┐
                       │  Nginx Proxy  │ (Exposes 80/443, terminates SSL)
                       └───────┬───────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
   ┌─────────────────┐ ┌──────────────┐ ┌───────────────────┐
   │  Dashboard UI   │ │ Backend API  │ │ Ingestion Service │
   │   (Port 5007)   │ │ (Port 8000)  │ │     (Daemon)      │
   └─────────────────┘ └───────┬──────┘ └─────────┬─────────┘
                               │                  │
                               └────────┬─────────┘
                                        │
                                        ▼
                               ┌─────────────────┐
                               │    InfluxDB     │ (Port 8086, internal only)
                               └─────────────────┘
                                        ▲
                                        │ (Writes points)
                               ┌────────┴────────┐
                               │    Mosquitto    │ (Port 1883, IoT broker)
                               └─────────────────┘
```

---

## File Contents

- [docker-compose.yml](docker-compose.yml): Coordinates and starts Nginx, Certbot, Mosquitto, InfluxDB, API, and Ingestion.
- [.env.prod.example](.env.prod.example): Environment template for setting domains, buckets, API tokens, and JWT keys.
- [nginx/nginx.conf](nginx/nginx.conf): Global performance configurations for Nginx.
- [nginx/conf.d/co2-system.conf](nginx/conf.d/co2-system.conf): Router mapping URLs and handling WebSocket protocol upgrades.
- [scripts/generate_certs.sh](scripts/generate_certs.sh): Script for generating self-signed certificates for local testing.
- [scripts/deploy.sh](scripts/deploy.sh): Orchestrates pull, container builds, and recreation sequences.
- [scripts/backup.sh](scripts/backup.sh): Generates gzipped snapshots of InfluxDB.

---

## Step-by-Step Installation Guide

Follow these steps to deploy the system on your VM/VPS host:

### Step 1: Clone and Prepare Configs
On your target server, clone the repository and navigate to the deployment folder:
```bash
git clone https://github.com/Cky200/co2-iot-lstm-ventilation-system.git
cd co2-iot-lstm-ventilation-system/phase10_deployment
```
Copy the template variables file:
```bash
cp .env.prod.example .env
```
Open `.env` and configure:
1. `DOMAIN_NAME`: Set to your registered FQDN (e.g., `co2.yourdomain.com`).
2. `CERTBOT_EMAIL`: Set to your admin contact email.
3. `INFLUXDB_INIT_PASSWORD`: Change to a secure database password.
4. `INFLUXDB_TOKEN`: Change to a secure random API token.
5. `SECRET_KEY` & `DASHBOARD_SECRET_KEY`: Set to strong cryptographic signing keys.

---

### Step 2: SSL Certificate Provisioning

Nginx requires valid certificates to start. Use **Option A** for live deployment or **Option B** for local staging.

#### Option A: Live Production (Let's Encrypt & Certbot)
To obtain Let's Encrypt certificates without starting Nginx (chicken-and-egg problem), we provision dummy certs first:
1. Generate temporary self-signed certs (validating domain name from `.env`):
   ```bash
   ./scripts/generate_certs.sh
   ```
2. Start the Nginx proxy and databases to open up HTTP challenge routing:
   ```bash
   docker compose up -d nginx influxdb mosquitto
   ```
3. Run Certbot to overwrite the dummy certificates with official Let's Encrypt certificates:
   ```bash
   # Load variables
   source .env
   
   # Run Certbot challenge
   docker compose run --rm certbot certonly --webroot -w /var/www/certbot \
     -d $DOMAIN_NAME --email $CERTBOT_EMAIL --agree-tos --no-eff-email --force-renewal
   ```
4. Reload Nginx to load the newly obtained Let's Encrypt certificates:
   ```bash
   docker compose exec nginx nginx -s reload
   ```

#### Option B: Staging/Offline Simulation (Self-Signed Certificates)
If you are running the production compose stack locally for validation:
1. Generate the self-signed certificates:
   ```bash
   ./scripts/generate_certs.sh
   ```
2. Open `docker-compose.yml` and modify the Nginx volume mapping to use your generated local cert directory instead of the named volume:
   ```yaml
   # Change Nginx volumes under 'nginx:' service:
   # - certbot_certs:/etc/letsencrypt:ro
   # TO:
   - ./nginx/certs:/etc/letsencrypt:ro
   ```

---

### Step 3: Run the Deploy Script
Execute the deployment automation to fetch, rebuild, and launch the rest of the services (Ingestion, Backend API, Dashboard UI):
```bash
./scripts/deploy.sh
```

Once completed:
- Nginx routes all HTTP requests on port 80 to HTTPS on port 443.
- FastAPI docs will be visible at: `https://yourdomain.com/docs`.
- Dashboard UI will be visible at: `https://yourdomain.com/`.

---

## MQTT Configuration for IoT Devices

For physical IoT devices (like Raspberry Pi sensors running Phase 5/Phase 6 code) to publish data to the server:
1. Ensure port `1883` on your host server is open to inbound traffic (configure firewall/security groups).
2. Configure your firmware script's host value to your server's public IP address or Domain Name:
   ```python
   # In your IoT configuration (phase5_iot_firmware/iot_firmware/config.py)
   # Set the broker IP to your server domain
   MQTT_BROKER = "yourdomain.com"
   ```

---

## Maintenance & Backups

### 1. Database Backups
To automate daily gzipped database backups, configure a cron job on the host machine:
1. Open the crontab editor:
   ```bash
   crontab -e
   ```
2. Add the following entry to execute backups every day at 2:00 AM:
   ```cron
   0 2 * * * /bin/bash /absolute/path/to/phase10_deployment/scripts/backup.sh >> /var/log/co2_backup.log 2>&1
   ```

### 2. View Service Logs
Verify container states and inspect output streams:
```bash
# View all container states
docker compose ps

# Follow backend logs
docker compose logs -f co2-backend

# Follow UI dashboard logs
docker compose logs -f co2-dashboard
```

### 3. Database Management
InfluxDB UI is unexposed to public ports for security. If you need to access the InfluxDB UI:
1. Establish a secure SSH tunnel from your local computer to the remote host:
   ```bash
   ssh -L 8086:localhost:8086 username@your-server-ip
   ```
2. Open your web browser locally and navigate to: `http://localhost:8086`.
