import time
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.api.dependencies import get_db_client
from src.api.routers import auth, co2, websocket
from src.utils.logger import get_logger
from src.utils.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION

logger = get_logger(__name__)

app = FastAPI(
    title="Hybrid IoT-LSTM CO2 Monitoring API",
    description="REST and WebSocket API for real-time and historical CO2 telemetry",
    version="1.0.0"
)

# CORS Middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this to frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request monitoring middleware
@app.middleware("http")
async def prometheus_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    path = request.url.path
    # Exclude metrics and health endpoints from standard request metrics
    if path not in {"/metrics", "/health", "/healthz"}:
        method = request.method
        status = str(response.status_code)
        HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=path, status=status).inc()
        HTTP_REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)
        
    return response

# Include routers
app.include_router(auth.router)
app.include_router(co2.router)
app.include_router(websocket.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the CO2 Monitoring API. Visit /docs for documentation."}

@app.get("/health")
def health(db = Depends(get_db_client)):
    """
    Health check endpoint verifying internal services and connections.
    """
    services_status = {}
    db_healthy = False
    try:
        if db is not None and db.client.ping():
            db_healthy = True
            services_status["database"] = "healthy"
        else:
            services_status["database"] = "unhealthy"
    except Exception as e:
        logger.error(f"Health check failed database verification: {e}")
        services_status["database"] = "unhealthy"

    if not db_healthy:
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "services": services_status}
        )

    return {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "services": services_status
    }

@app.get("/metrics")
def metrics():
    """
    Prometheus metrics scraping endpoint.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
