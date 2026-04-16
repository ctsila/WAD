from llama_cpp import Llama

from app.config import settings

_llm: Llama | None = None


def get_llm() -> Llama:
    global _llm
    if _llm is None:
        _llm = Llama(model_path=settings.LLM_MODEL_PATH, n_ctx=512, n_threads=4)
    return _llm


def generate_response(prompt: str) -> str:
    llm = get_llm()
    result = llm(prompt, max_tokens=200, stream=False)
    return result["choices"][0]["text"]


async def stream_response(prompt: str):
    llm = get_llm()
    stream = llm(prompt, max_tokens=200, stream=True)
    for chunk in stream:
        token = chunk["choices"][0]["text"]
        if token:
            yield token
