from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, oauth2_scheme
from app.models.user import User
from app.schemas.auth import AuthMeResponse, LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_github_oauth_url,
    handle_github_callback,
    refresh_access_token,
    register_user,
    revoke_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, payload.username, payload.email, payload.password)
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = await create_refresh_token(user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = await create_refresh_token(user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest):
    access_token = await refresh_access_token(payload.refresh_token)
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(
    payload: RefreshRequest,
    _: str = Depends(oauth2_scheme),
    __: User = Depends(get_current_user),
):
    await revoke_refresh_token(payload.refresh_token)
    return {"message": "Logged out"}


@router.get("/me", response_model=AuthMeResponse)
async def me(current_user: User = Depends(get_current_user)):
    return AuthMeResponse(id=str(current_user.id), username=current_user.username, email=current_user.email)


@router.get("/github")
async def github_login():
    url = await get_github_oauth_url()
    return RedirectResponse(url)


@router.get("/github/callback", response_model=TokenResponse)
async def github_callback(code: str, db: AsyncSession = Depends(get_db)):
    try:
        user = await handle_github_callback(db, code)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = await create_refresh_token(user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
