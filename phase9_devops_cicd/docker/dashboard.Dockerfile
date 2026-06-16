# ==========================================
# Stage 1: Build dependencies
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /app

COPY phase7_dashboard_ui/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==========================================
# Stage 2: Final runtime container
# ==========================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Copy installed libraries from the builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy dashboard application files
COPY phase7_dashboard_ui/dashboard_ui/ /app/dashboard_ui/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create a non-privileged user to run the application
RUN adduser --disabled-password --no-create-home --gecos "" appuser && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /root/.local

USER appuser

EXPOSE 5007

# Start the Flask dashboard UI application
CMD ["python", "-m", "dashboard_ui.main"]
