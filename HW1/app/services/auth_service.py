import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status

from app.config import settings
from app.models.user import User
from app.redis_client import get_redis

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def _create_jwt_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def register_user(db: AsyncSession, username: str, email: str, password: str) -> User:
    normalized_username = username.strip()
    normalized_email = email.strip().lower()

    existing_by_username = await db.execute(select(User).where(User.username == normalized_username))
    if existing_by_username.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username is already taken")

    existing_by_email = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
    if existing_by_email.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    hashed_password = pwd_context.hash(password)
    user = User(username=normalized_username, email=normalized_email, hashed_password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    identifier = username.strip()
    result = await db.execute(
        select(User).where(
            or_(
                User.username == identifier,
                func.lower(User.email) == identifier.lower(),
            )
        )
    )
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password:
        return None
    if not pwd_context.verify(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    expires = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_jwt_token(data, expires)


async def create_refresh_token(user_id: UUID) -> str:
    token = secrets.token_urlsafe(48)
    ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    redis = get_redis()
    await redis.setex(f"refresh:{token}", ttl_seconds, str(user_id))
    return token


async def refresh_access_token(refresh_token: str) -> str | None:
    redis = get_redis()
    user_id = await redis.get(f"refresh:{refresh_token}")
    if not user_id:
        return None
    return create_access_token({"sub": user_id})


async def revoke_refresh_token(refresh_token: str) -> None:
    redis = get_redis()
    await redis.delete(f"refresh:{refresh_token}")


async def get_github_oauth_url() -> str:
    return (
        "https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        "&scope=read:user user:email"
    )


async def handle_github_callback(db: AsyncSession, code: str) -> User:
    async with httpx.AsyncClient(timeout=20) as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
        )
        token_resp.raise_for_status()
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise ValueError("GitHub token exchange failed")

        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        )
        user_resp.raise_for_status()
        profile = user_resp.json()

        emails_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        )
        primary_email = None
        if emails_resp.status_code == 200:
            emails = emails_resp.json()
            primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
            primary_email = (primary or (emails[0] if emails else {})).get("email")

    github_id = str(profile.get("id"))
    username = profile.get("login") or f"github_{github_id}"
    email = primary_email or profile.get("email") or f"{username}@users.noreply.github.com"

    by_github = await db.execute(select(User).where(User.github_id == github_id))
    user = by_github.scalar_one_or_none()
    if user:
        return user

    by_email = await db.execute(select(User).where(User.email == email))
    user_by_email = by_email.scalar_one_or_none()
    if user_by_email:
        user_by_email.github_id = github_id
        if not user_by_email.username:
            user_by_email.username = username
        await db.commit()
        await db.refresh(user_by_email)
        return user_by_email

    user = User(username=username, email=email, github_id=github_id, hashed_password=None)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
