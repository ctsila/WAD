from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.controllers.auth_controller import router as auth_router
from app.controllers.chat_controller import router as chat_router
from app.controllers.message_controller import router as message_router
from app.database import AsyncSessionLocal
from app.redis_client import get_redis

from llama_cpp import Llama
from huggingface_hub import hf_hub_download
import os
import shutil


HF_REPO_ID = "Jackrong/Qwen3.5-4B-Claude-4.6-Opus-Reasoning-Distilled-GGUF"
HF_FILENAME = "Qwen3.5-4B.Q2_K.gguf"


def create_app() -> FastAPI:
    app = FastAPI(title="LLM Chat App")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def load_llm():
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_model_path = os.path.join(base_dir, "model.gguf")

        if not os.path.exists(target_model_path):
            print("model.gguf not found, downloading from Hugging Face...")
            downloaded_path = hf_hub_download(
                repo_id=HF_REPO_ID,
                filename=HF_FILENAME,
                local_dir=base_dir,
                local_dir_use_symlinks=False,
            )

            if downloaded_path != target_model_path:
                shutil.copyfile(downloaded_path, target_model_path)

            print(f"Model saved to: {target_model_path}")

        if not hasattr(app.state, "llm"):
            print("Loading GGUF model...")
            app.state.llm = Llama(
                model_path=target_model_path,
                n_ctx=4096,
                n_threads=4,
            )
            print("Model loaded")

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
