import json
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message, MessageRole
from app.redis_client import get_redis


def _serialize_messages(messages: list[Message]) -> str:
    payload = [
        {
            "id": str(m.id),
            "chat_id": str(m.chat_id),
            "role": m.role.value if hasattr(m.role, "value") else str(m.role),
            "content": m.content,
            "created_at": m.created_at.isoformat() if isinstance(m.created_at, datetime) else str(m.created_at),
        }
        for m in messages
    ]
    return json.dumps(payload)


def _deserialize_messages(raw: str) -> list[dict]:
    return json.loads(raw)


async def add_message(db: AsyncSession, chat_id: UUID, role: str, content: str) -> Message:
    message = Message(chat_id=chat_id, role=MessageRole(role), content=content)
    db.add(message)
    await db.commit()
    await db.refresh(message)

    redis = get_redis()
    await redis.delete(f"chat_messages:{chat_id}")
    return message


async def get_chat_messages(db: AsyncSession, chat_id: UUID) -> list[Message] | list[dict]:
    redis = get_redis()
    cache_key = f"chat_messages:{chat_id}"
    cached = await redis.get(cache_key)
    if cached:
        return _deserialize_messages(cached)

    result = await db.execute(select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.asc()))
    messages = list(result.scalars().all())
    await redis.setex(cache_key, 300, _serialize_messages(messages))
    return messages
