from .local_llm import get_local_llm, LLM
from .mock_llm import MockLLM

def get_llm(mode: str = "mock"):  # Default to mock for testing
    if mode == "local":
        try:
            return get_local_llm()
        except Exception as e:
            print(f"Warning: Could not load local LLM: {e}")
            print("Falling back to MockLLM")
            return MockLLM()
    # Default to mock for testing
    return MockLLM()
