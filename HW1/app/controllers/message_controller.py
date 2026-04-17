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
from app.services.llm_service import generate_response, get_llm, stream_response
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
    await add_message(db, chat_id, "user", payload.question)
    prompt = f"User: {payload.question}\nAssistant:"

    if not payload.stream:
        try:
            answer = generate_response(prompt)
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"LLM is unavailable: {exc}") from exc
        await add_message(db, chat_id, "assistant", answer)
        return AskResponse(answer=answer)

    try:
        get_llm()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"LLM is unavailable: {exc}") from exc

    async def event_generator() -> AsyncGenerator[str, None]:
        full_answer: list[str] = []
        async for token in stream_response(prompt):
            full_answer.append(token)
            yield f"data: {token}\n\n"
        final_text = "".join(full_answer)
        await add_message(db, chat_id, "assistant", final_text)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
