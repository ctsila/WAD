import os
from llama_cpp import Llama

from app.config import settings

_llm: Llama | None = None
_llm_load_failed: bool = False


def _clean_response_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("Assistant:"):
        cleaned = cleaned[len("Assistant:") :].strip()

    stop_markers = ["\nUser:", "\nAssistant:", "\nSystem:", " User:", " Assistant:", " System:"]
    cut_positions = [cleaned.find(marker) for marker in stop_markers if cleaned.find(marker) != -1]
    if cut_positions:
        cleaned = cleaned[: min(cut_positions)].rstrip()
    return cleaned


def get_llm() -> Llama:
    global _llm, _llm_load_failed
    if _llm_load_failed:
        raise RuntimeError(f"Model path does not exist: {settings.LLM_MODEL_PATH}")
    
    if _llm is None:
        if not os.path.exists(settings.LLM_MODEL_PATH):
            _llm_load_failed = True
            raise RuntimeError(f"Model path does not exist: {settings.LLM_MODEL_PATH}")
        _llm = Llama(model_path=settings.LLM_MODEL_PATH, n_ctx=2048, n_threads=4)
    return _llm


def generate_response(prompt: str) -> str:
    try:
        llm = get_llm()
        result = llm(
            prompt,
            max_tokens=220,
            stream=False,
            stop=["\nUser:", "\nSystem:", "\nAssistant:", "User:", "System:", "Assistant:"],
        )
        text = result["choices"][0]["text"]
        cleaned = _clean_response_text(text)
        return cleaned or "I'm not sure yet. Please try rephrasing your question."
    except Exception as exc:
        print(f"LLM generation error: {exc}")
        # Model not available, return a stub response
        return "I'm sorry, the LLM model is not currently available. Please try again later or ensure the model file is present."


async def stream_response(prompt: str):
    try:
        llm = get_llm()
        stream = llm(
            prompt,
            max_tokens=220,
            stream=True,
            stop=["\nUser:", "\nSystem:", "\nAssistant:", "User:", "System:", "Assistant:"],
        )
        for chunk in stream:
            token = chunk["choices"][0]["text"]
            if token:
                yield token
    except Exception as exc:
        print(f"LLM streaming error: {exc}")
        # Model not available, yield a stub response
        yield "I'm sorry, the LLM model is not currently available. Please try again later or ensure the model file is present."
