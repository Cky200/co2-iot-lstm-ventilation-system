from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import auth, co2, websocket
from src.utils.logger import get_logger

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

# Include routers
app.include_router(auth.router)
app.include_router(co2.router)
app.include_router(websocket.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the CO2 Monitoring API. Visit /docs for documentation."}
