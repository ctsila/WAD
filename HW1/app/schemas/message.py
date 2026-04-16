from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: UUID
    chat_id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class AskRequest(BaseModel):
    question: str
    stream: bool = False


class AskResponse(BaseModel):
    answer: str
