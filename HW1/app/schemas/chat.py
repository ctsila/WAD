from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class ChatCreateRequest(BaseModel):
    title: str | None = "New Chat"


class ChatRenameRequest(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        title = value.strip()
        if len(title) < 1:
            raise ValueError("Chat title cannot be empty")
        if len(title) > 80:
            raise ValueError("Chat title must be 80 characters or fewer")
        return title


class ChatResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
