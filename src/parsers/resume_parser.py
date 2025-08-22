from dataclasses import dataclass
from typing import Optional
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document
import os

@dataclass
class ResumeProfile:
    name: str | None
    email: str | None
    phone: str | None
    skills: list[str]
    summary: Optional[str]
    raw_text: str

def _extract_text(path: str) -> str:
    if path.lower().endswith(".pdf"):
        return pdf_extract_text(path) or ""
    elif path.lower().endswith(".docx"):
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

def parse_resume(path: str) -> ResumeProfile:
    text = _extract_text(path)
    # Primitive heuristics; LLM will refine during tailoring
    import re
    email = None
    m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    if m: email = m.group(0)
    phone = None
    m2 = re.search(r"(?:\+?\d[\s-]?){8,15}", text)
    if m2: phone = m2.group(0)
    # skill guess
    skills = []
    for kw in ["python","pytorch","tensorflow","scikit","ml","ai","nlp","cv","react","node","mongodb","docker","aws","fastapi","gensim","transformers","llm","langchain"]:
        if re.search(rf"\b{re.escape(kw)}\b", text.lower()):
            skills.append(kw)
    name = None
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines: name = lines[0] if len(lines[0].split())<=5 else None
    summary = None
    return ResumeProfile(name=name, email=email, phone=phone, skills=skills, summary=summary, raw_text=text)
