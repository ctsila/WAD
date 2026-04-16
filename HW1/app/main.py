from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.controllers.auth_controller import router as auth_router
from app.controllers.chat_controller import router as chat_router
from app.controllers.message_controller import router as message_router
from app.database import AsyncSessionLocal
from app.redis_client import get_redis


def create_app() -> FastAPI:
    app = FastAPI(title="LLM Chat App")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="", tags=["auth"])
    app.include_router(chat_router, prefix="", tags=["chats"])
    app.include_router(message_router, prefix="", tags=["messages"])

    @app.get("/health")
    async def health_check():
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        redis = get_redis()
        await redis.ping()
        return {"status": "ok", "db": "connected", "redis": "connected"}

    return app


app = create_app()
