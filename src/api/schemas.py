from datetime import datetime

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

class CO2DataPoint(BaseModel):
    time: datetime
    ppm: float
    voltage: float
    relay_state: bool

class CO2HistoryResponse(BaseModel):
    data: list[CO2DataPoint]
