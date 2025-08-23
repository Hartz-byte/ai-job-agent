from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

class Config(BaseModel):
    llm_mode: str = os.getenv("LLM_MODE", "local")
    llama_model_path: str = os.getenv("LLAMA_MODEL_PATH", "./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf")
    llama_ctx: int = int(os.getenv("LLAMA_CTX", "4096"))
    llama_n_threads: int = int(os.getenv("LLAMA_N_THREADS", "6"))
    llama_n_gpu_layers: int = int(os.getenv("LLAMA_N_GPU_LAYERS", "20"))

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    resume_path: str = os.getenv("RESUME_PATH", "./data/resume.pdf")
    resume_template_path: str = os.getenv("RESUME_TEMPLATE_PATH", "")
    cover_letter_base_path: str = os.getenv("COVER_LETTER_BASE_PATH", "./data/cover_letter_base.docx")

    countries: list[str] = [c.strip() for c in os.getenv("COUNTRIES", "India").split(",") if c.strip()]
    cities: list[str] = [c.strip() for c in os.getenv("CITIES", "").split(",") if c.strip()]
    remote_ok: bool = os.getenv("REMOTE_OK", "true").lower() == "true"
    remote_global_ok: bool = os.getenv("REMOTE_GLOBAL_OK", "true").lower() == "true"
    keywords: list[str] = [k.strip() for k in os.getenv("KEYWORDS", "machine learning,ml engineer").split(",") if k.strip()]

    enable_linkedin: bool = os.getenv("ENABLE_LINKEDIN", "true").lower() == "true"
    enable_indeed: bool = os.getenv("ENABLE_INDEED", "true").lower() == "true"
    enable_wellfound: bool = os.getenv("ENABLE_WELLFOUND", "true").lower() == "true"
    enable_internshala: bool = os.getenv("ENABLE_INTERNSHALA", "true").lower() == "true"

    apply_linkedin_easy_apply: bool = os.getenv("APPLY_LINKEDIN_EASY_APPLY", "true").lower() == "true"
    apply_internshala: bool = os.getenv("APPLY_INTERNSHALA", "true").lower() == "true"
    apply_wellfound: bool = os.getenv("APPLY_WELLFOUND", "true").lower() == "true"
    apply_indeed: bool = os.getenv("APPLY_INDEED", "false").lower() == "true"

    requests_per_min: int = int(os.getenv("REQUESTS_PER_MIN", "16"))
    db_path: str = os.getenv("DB_PATH", "./agent.db")

cfg = Config()
