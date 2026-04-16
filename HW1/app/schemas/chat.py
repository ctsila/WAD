from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ChatCreateRequest(BaseModel):
    title: str | None = "New Chat"


class ChatResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
