import re

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        username = value.strip()
        if not re.fullmatch(r"[A-Za-z0-9._-]{3,24}", username):
            raise ValueError(
                "Username must be 3-24 characters and use only letters, numbers, dot, underscore, or hyphen"
            )
        return username

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        password = value.strip()
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            raise ValueError("Password must include at least one letter and one number")
        return password


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_login_identifier(cls, value: str) -> str:
        identifier = value.strip()
        if len(identifier) < 3:
            raise ValueError("Username or email is too short")
        return identifier

    @field_validator("password")
    @classmethod
    def validate_login_password(cls, value: str) -> str:
        password = value.strip()
        if not password:
            raise ValueError("Password is required")
        return password


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class AuthMeResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
