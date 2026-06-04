from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class CO2DataPoint(BaseModel):
    time: datetime
    ppm: float
    voltage: float
    relay_state: bool

class CO2HistoryResponse(BaseModel):
    data: List[CO2DataPoint]
