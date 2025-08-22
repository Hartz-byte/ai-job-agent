from .local_llm import get_local_llm, LLM

def get_llm(mode: str = "local"):
    if mode == "local":
        return get_local_llm()
    # Fallbacks can be added here (OpenAI etc.)
    return get_local_llm()
