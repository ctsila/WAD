from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.message import AskRequest, AskResponse
from app.services.chat_service import get_chat
from app.services.llm_service import generate_response, stream_response
from app.services.message_service import add_message, get_chat_messages

router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["messages"])


@router.get("")
async def list_messages(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_chat(db, chat_id, current_user.id)
    return await get_chat_messages(db, chat_id)


@router.post("/ask")
async def ask_question(
    chat_id: UUID,
    payload: AskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_chat(db, chat_id, current_user.id)
    history = await get_chat_messages(db, chat_id)

    def get_role(msg):
        role = msg.get("role") if isinstance(msg, dict) else msg.role
        return role.value if hasattr(role, "value") else str(role)

    def get_content(msg):
        return msg.get("content") if isinstance(msg, dict) else msg.content

    turns: list[str] = [
        "System: You are a helpful assistant. Reply naturally and do not include role labels like User: or Assistant:."
    ]
    for msg in history:
        role = get_role(msg)
        content = (get_content(msg) or "").strip()
        if not content:
            continue
        if role == "user":
            turns.append(f"User: {content}")
        elif role == "assistant":
            turns.append(f"Assistant: {content}")

    user_question = payload.question.strip()
    turns.append(f"User: {user_question}")
    turns.append("Assistant:")
    prompt = "\n".join(turns)

    await add_message(db, chat_id, "user", user_question)

    if not payload.stream:
        answer = generate_response(prompt)
        await add_message(db, chat_id, "assistant", answer)
        return AskResponse(answer=answer)

    async def event_generator() -> AsyncGenerator[str, None]:
        full_answer: list[str] = []
        async for token in stream_response(prompt):
            full_answer.append(token)
            yield f"data: {token}\n\n"
        final_text = "".join(full_answer)
        await add_message(db, chat_id, "assistant", final_text)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
