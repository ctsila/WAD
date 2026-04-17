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

# здесь можно прописать любую модель/файл из Hugging Face GGUF
HF_REPO_ID = "mradermacher/Gemma-4-Queen-31B-it-GGUF"
HF_FILENAME = "Gemma-4-Queen-31B-it.Q4_K_S.gguf"  # точное имя .gguf из вкладки Files на HF


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
        """
        1) если model.gguf нет — скачиваем нужный .gguf из HF
        2) кладём его в корень HW1 как model.gguf
        3) загружаем Llama и сохраняем в app.state.llm
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_model_path = os.path.join(base_dir, "model.gguf")

        # шаг 1: скачивание и "переименование"
        if not os.path.exists(target_model_path):
            print("model.gguf not found, downloading from Hugging Face...")

            downloaded_path = hf_hub_download(
                repo_id=HF_REPO_ID,
                filename=HF_FILENAME,
                local_dir=base_dir,          # скачиваем именно в HW1
                local_dir_use_symlinks=False
            )

            # если файл скачался под другим именем — копируем как model.gguf
            if downloaded_path != target_model_path:
                shutil.copyfile(downloaded_path, target_model_path)

            print(f"Model saved to: {target_model_path}")

        # шаг 2: загрузка модели один раз
        if not hasattr(app.state, "llm"):
            print("Loading GGUF model into llama_cpp...")
            app.state.llm = Llama(
                model_path=target_model_path,
                n_ctx=4096,
                n_threads=4,
                # при необходимости настроишь chat_format и прочие параметры под конкретную модель
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
