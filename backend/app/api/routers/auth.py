from fastapi import APIRouter, HTTPException

from app.schemas.auth import TokenResponse, UserCreate, UserLogin
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(payload: UserCreate) -> dict[str, str]:
    auth_service.register(payload.email, payload.password)
    return {"status": "registered"}


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin) -> TokenResponse:
    if not auth_service.authenticate(payload.email, payload.password):
        raise HTTPException(status_code=401, detail="invalid credentials")
    token = auth_service.create_token(payload.email)
    return TokenResponse(access_token=token)
