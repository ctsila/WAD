from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatCreateRequest, ChatRenameRequest, ChatResponse
from app.services.chat_service import create_chat, delete_chat, get_chat, get_user_chats, rename_chat
from app.services.llm_service import get_llm
from app.services.message_service import get_chat_messages

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("", response_model=ChatResponse)
async def create_chat_endpoint(
    payload: ChatCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = await create_chat(db, current_user.id, payload.title or "New Chat")
    return chat


@router.get("", response_model=list[ChatResponse])
async def list_chats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_user_chats(db, current_user.id)


@router.get("/{chat_id}")
async def get_chat_endpoint(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = await get_chat(db, chat_id, current_user.id)
    messages = await get_chat_messages(db, chat_id)
    return {"chat": ChatResponse.model_validate(chat), "messages": messages}


@router.delete("/{chat_id}")
async def delete_chat_endpoint(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await delete_chat(db, chat_id, current_user.id)
    return {"message": "Chat deleted"}


@router.patch("/{chat_id}", response_model=ChatResponse)
async def rename_chat_endpoint(
    chat_id: UUID,
    payload: ChatRenameRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = await rename_chat(db, chat_id, current_user.id, payload.title)
    return chat


@router.get("/{chat_id}/ask")
async def ask_llm_in_chat(
    chat_id: UUID,
    question: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Ensure user has access to the chat.
    await get_chat(db, chat_id, current_user.id)

    try:
        llm = get_llm()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"LLM is unavailable: {exc}") from exc

    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": question}],
        max_tokens=256,
        temperature=0.7,
    )

    answer = response["choices"][0]["message"]["content"]
    return {"question": question, "answer": answer}
