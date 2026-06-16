# ==========================================
# Stage 1: Build dependencies in a virtual environment
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies for compilation of packages like bcrypt/cryptography if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==========================================
# Stage 2: Final runtime container
# ==========================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Copy installed libraries from the builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy source code
COPY src/ /app/src/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create a non-privileged user to run the application
RUN adduser --disabled-password --no-create-home --gecos "" appuser && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /root/.local

USER appuser

EXPOSE 8000

# Default command is to run the FastAPI server.
# For ingestion, this container can be started with command: python -m src.pipeline.ingestion
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
