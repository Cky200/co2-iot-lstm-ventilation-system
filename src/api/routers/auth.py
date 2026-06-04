from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from src.api.dependencies import (
    ACCESS_TOKEN_EXPIRE_MINUTES, 
    create_access_token,
    mock_users_db,
    verify_password
)
from src.api.schemas import Token

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # We must implement authenticate_user logic here or in dependencies
    user = None
    if form_data.username in mock_users_db:
        db_user = mock_users_db[form_data.username]
        if verify_password(form_data.password, db_user["hashed_password"]):
            user = db_user
            
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
