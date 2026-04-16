from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat


async def create_chat(db: AsyncSession, user_id: UUID, title: str = "New Chat") -> Chat:
    chat = Chat(user_id=user_id, title=title or "New Chat")
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat


async def get_user_chats(db: AsyncSession, user_id: UUID) -> list[Chat]:
    result = await db.execute(select(Chat).where(Chat.user_id == user_id).order_by(Chat.updated_at.desc()))
    return list(result.scalars().all())


async def get_chat(db: AsyncSession, chat_id: UUID, user_id: UUID) -> Chat:
    result = await db.execute(select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return chat


async def delete_chat(db: AsyncSession, chat_id: UUID, user_id: UUID) -> None:
    chat = await get_chat(db, chat_id, user_id)
    await db.delete(chat)
    await db.commit()
