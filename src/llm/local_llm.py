from dataclasses import dataclass
from llama_cpp import Llama
from config import cfg

@dataclass
class LLM:
    def generate(self, prompt: str, max_tokens: int = 768, temperature: float = 0.6) -> str:
        raise NotImplementedError

class LocalMistral(LLM):
    def __init__(self):
        self.llm = Llama(
            model_path=cfg.llama_model_path,
            n_ctx=cfg.llama_ctx,
            n_threads=cfg.llama_n_threads,
            n_gpu_layers=cfg.llama_n_gpu_layers,
            verbose=False
        )

    def generate(self, prompt: str, max_tokens: int = 768, temperature: float = 0.6) -> str:
        # Simple instruct format without duplicate BOS token
        if prompt.lstrip().startswith("<s>"):
            prompt = prompt.lstrip()[3:].lstrip()
        full = f"[INST] {prompt} [/INST]"
        out = self.llm(
            full,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["</s>", "[INST]"]
        )
        return out["choices"][0]["text"].strip()

def get_local_llm() -> LLM:
    return LocalMistral()
