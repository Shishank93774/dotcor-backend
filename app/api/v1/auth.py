from app.core.services import get_auth_service
from app.schemas.auth import AuthCreate, AuthRead
from app.services.auth import AuthService
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthRead, status_code=status.HTTP_200_OK)
async def login(auth: AuthCreate, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.login(**auth.model_dump())
