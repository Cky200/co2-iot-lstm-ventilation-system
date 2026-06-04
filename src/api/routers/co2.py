from fastapi import APIRouter, Depends, Query
from src.api.dependencies import get_current_active_user, get_db_client
from src.api.schemas import User, CO2HistoryResponse
from src.pipeline.db_client import InfluxDBWrapper

router = APIRouter(
    prefix="/api/v1/co2",
    tags=["co2"]
)

@router.get("/history", response_model=CO2HistoryResponse)
async def get_co2_history(
    minutes_back: int = Query(60, description="Minutes of historical data to retrieve"),
    current_user: User = Depends(get_current_active_user),
    db: InfluxDBWrapper = Depends(get_db_client)
):
    """
    Fetches historical CO2 data from InfluxDB.
    Requires authentication.
    """
    raw_data = db.query_recent_data(minutes_back)
    # The raw_data list maps cleanly to CO2DataPoint schemas
    return {"data": raw_data}
