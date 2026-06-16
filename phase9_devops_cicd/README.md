# Phase 9: DevOps CI/CD & Infrastructure

This package delivers the Continuous Integration (CI), Continuous Deployment (CD), containerization, and code quality automation structures for the **Hybrid IoT–LSTM CO₂ Monitoring and Automated Ventilation Control System**.

---

## Architecture Overview

The DevOps topology consists of three primary branches:
1. **Linting and Static Analysis**: Unified checks using Ruff (linter/formatter) and MyPy (type checking).
2. **Docker Containerization**: Portable container definitions for the Backend API, Ingestion daemon, Dashboard UI, Database (InfluxDB), and MQTT Broker (Mosquitto).
3. **Automated Pipelines (GitHub Actions)**: Workflows running code quality, unit/integration testing, container builds, image pushing (GHCR), and orchestration simulation.

---

## Directory Structure

All configuration assets are located under `phase9_devops_cicd/` with workflows at the root `.github/` folder:

```
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Main CI testing, linting, and coverage workflow
│       ├── docker-build.yml       # Verification workflow for Docker builds
│       └── cd.yml                 # CD publishing to GHCR and deploy orchestrator
└── phase9_devops_cicd/
    ├── README.md                  # This documentation guide
    ├── config/
    │   ├── ruff.toml              # Ruff linting & formatting rules
    │   └── mypy.ini               # MyPy static type analysis settings
    └── docker/
        ├── backend.Dockerfile     # Multi-stage image for FastAPI API & Ingestion daemon
        ├── dashboard.Dockerfile   # Flask + Socket.IO dashboard image
        └── docker-compose.prod.yml # Production multi-service orchestration spec
```

---

## Code Quality Standards

Code checks enforce formatting, styling conventions, and static typing rules:

### 1. Ruff (Linter & Formatter)
Ruff replaces flake8, black, and isort, running code analysis 10-100x faster.
- **Config file**: [ruff.toml](config/ruff.toml)
- **Commands**:
  ```bash
  # Check code style and rules
  ruff check --config phase9_devops_cicd/config/ruff.toml .
  
  # Automatically fix warnings
  ruff check --config phase9_devops_cicd/config/ruff.toml . --fix
  
  # Check formatting compliance
  ruff format --config phase9_devops_cicd/config/ruff.toml --check .
  ```

### 2. MyPy (Type Safety)
Type checking validates return values and function parameters using strict annotations.
- **Config file**: [mypy.ini](config/mypy.ini)
- **Command**:
  ```bash
  mypy --config-file phase9_devops_cicd/config/mypy.ini src/ phase5_iot_firmware/iot_firmware/ phase6_ventilation_control/ventilation_control/ phase7_dashboard_ui/dashboard_ui/
  ```

---

## Docker Containerization

Production deployment containerizes components using minimal, secure images.

### Dockerfiles
- **Backend Image** ([backend.Dockerfile](docker/backend.Dockerfile)):
  Uses a multi-stage build starting from `python:3.11-slim` with a `builder` layer that installs packages. The final `runner` layer runs as a non-privileged system user (`appuser`) for security compliance. It is used to run both the FastAPI API and the MQTT Ingestion daemon.
- **Dashboard Image** ([dashboard.Dockerfile](docker/dashboard.Dockerfile)):
  Runs the Flask + Socket.IO dashboard on port `5007`, copying assets under `/app/dashboard_ui` and running as a non-root user.

### Production Orchestration
The production setup coordinates InfluxDB, MQTT, API, Ingestion, and the UI using a private Docker bridge network.
- **Compose spec**: [docker-compose.prod.yml](docker/docker-compose.prod.yml)
- **How to run locally**:
  ```bash
  # Start the entire stack in the background
  docker compose -f phase9_devops_cicd/docker/docker-compose.prod.yml up -d
  
  # Verify logs of specific services
  docker compose -f phase9_devops_cicd/docker/docker-compose.prod.yml logs -f co2-backend
  
  # Shut down the stack and remove networks/containers
  docker compose -f phase9_devops_cicd/docker/docker-compose.prod.yml down
  ```

---

## CI/CD Workflows (GitHub Actions)

### 1. CI Pipeline (`ci.yml`)
Runs on push and pull requests to `main`.
1. **Linter & Formatter Check**: Executes Ruff checks.
2. **Type Safety Check**: Runs MyPy verification on source packages.
3. **Multi-Phase Pytest runner**: Executes core tests, IoT firmware tests, Ventilation controller tests, and Dashboard UI tests in isolation.
4. **Coverage XML Generator**: Runs Phase 8 coverage suite, exporting an XML report and uploading it to GHA artifacts.

### 2. Build Verification (`docker-build.yml`)
Runs on pull requests altering source modules or Docker configurations. It compiles local Docker images for both services to prevent registry build failures.

### 3. CD Pipeline (`cd.yml`)
Runs on push to `main` (after CI succeeds) or via manual trigger.
1. **Build & Tag**: Compiles optimized images with tags representing both the unique Git commit SHA (e.g., `:c243dae...`) and `:latest`.
2. **Publish**: Pushes the compiled images to the secure **GitHub Container Registry (GHCR)** at `ghcr.io/username/repository/*`.
3. **Deployment Trigger (Simulation)**: Prints deployment parameters. To automate a live release on your VM host:
   - Save your SSH private key under the repository secret `DEPLOY_SSH_KEY`.
   - Add a step to your CD job running an SSH command on the target host:
     ```bash
     docker compose -f phase9_devops_cicd/docker/docker-compose.prod.yml pull
     docker compose -f phase9_devops_cicd/docker/docker-compose.prod.yml up -d --remove-orphans
     ```
