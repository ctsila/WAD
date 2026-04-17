import os
from llama_cpp import Llama

from app.config import settings

_llm: Llama | None = None
_llm_load_failed: bool = False


def get_llm() -> Llama:
    global _llm, _llm_load_failed
    if _llm_load_failed:
        raise RuntimeError(f"Model path does not exist: {settings.LLM_MODEL_PATH}")
    
    if _llm is None:
        if not os.path.exists(settings.LLM_MODEL_PATH):
            _llm_load_failed = True
            raise RuntimeError(f"Model path does not exist: {settings.LLM_MODEL_PATH}")
        _llm = Llama(model_path=settings.LLM_MODEL_PATH, n_ctx=512, n_threads=4)
    return _llm


def generate_response(prompt: str) -> str:
    try:
        llm = get_llm()
        result = llm(prompt, max_tokens=200, stream=False)
        return result["choices"][0]["text"]
    except RuntimeError:
        # Model not available, return a stub response
        return "I'm sorry, the LLM model is not currently available. Please try again later or ensure the model file is present."


async def stream_response(prompt: str):
    try:
        llm = get_llm()
        stream = llm(prompt, max_tokens=200, stream=True)
        for chunk in stream:
            token = chunk["choices"][0]["text"]
            if token:
                yield token
    except RuntimeError:
        # Model not available, yield a stub response
        yield "I'm sorry, the LLM model is not currently available. Please try again later or ensure the model file is present."
