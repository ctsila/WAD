from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.controllers.auth_controller import router as auth_router
from app.controllers.chat_controller import router as chat_router
from app.controllers.message_controller import router as message_router
from app.database import AsyncSessionLocal
from app.redis_client import get_redis
from app.services.llm_service import get_llm


def create_app() -> FastAPI:
    app = FastAPI(title="LLM Chat App")

    raw_origins = settings.CORS_ALLOW_ORIGINS.strip()
    allow_origins = ["*"] if raw_origins == "*" else [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def preload_llm_if_enabled():
        if not settings.PRELOAD_LLM_ON_STARTUP:
            return

        try:
            print("PRELOAD_LLM_ON_STARTUP=true, loading model...")
            get_llm()
            print("Model loaded")
        except Exception as exc:
            # Do not block API startup if model loading fails.
            print(f"LLM preload failed, continuing without LLM: {exc}")

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
