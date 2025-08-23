import os
from docx import Document
from jinja2 import Template
from llm import get_llm
from llm.prompts import TAILOR_PROMPT, COVER_LETTER_PROMPT
from parsers.resume_parser import ResumeProfile
from storage.models import JobPost
from config import cfg

def _save_docx_paragraphs(paragraphs: list[str], out_path: str):
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    doc.save(out_path)

def _render_cover_letter_jinja(context: dict, out_path: str):
    with open(os.path.join(os.path.dirname(__file__), "cover_letter_template.jinja"), "r", encoding="utf-8") as f:
        template = Template(f.read())
    rendered = template.render(**context)
    doc = Document()
    for line in rendered.splitlines():
        doc.add_paragraph(line)
    doc.save(out_path)

def tailor_resume_and_cl(profile: ResumeProfile, job: JobPost, job_slug: str) -> tuple[str, str]:
    llm = get_llm(mode=cfg.llm_mode)
    job_text = job.description or job.title
    # Generate tailored content with richer context
    tailored = llm.generate(
        TAILOR_PROMPT.format(
            job_title=job.title or "",
            company=job.company or "",
            location=job.location or "",
            job_url=job.url or "",
            resume_text=profile.raw_text,
            job_text=job_text,
        ),
        max_tokens=900,
    )
    # parse sections with fallbacks
    summary, bullets, skills = "", [], ""
    import re
    s = tailored or ""
    sm = re.search(r"##\s*SUMMARY(.*?)(##|$)", s, flags=re.S|re.I)
    if sm and sm.group(1).strip():
        summary = sm.group(1).strip()
    bm = re.search(r"##\s*BULLETS(.*?)(##|$)", s, flags=re.S|re.I)
    if bm and bm.group(1).strip():
        bullets = [ln.strip("- ").strip() for ln in bm.group(1).strip().splitlines() if ln.strip()]
    km = re.search(r"##\s*SKILLS(.*?)(##|$)", s, flags=re.S|re.I)
    if km and km.group(1).strip():
        skills = km.group(1).strip()
    # Fallbacks if sections missing
    if not bullets:
        bullets = [ln.strip() for ln in s.splitlines() if ln.strip().startswith('-')][:8]
    if not summary:
        # Take first non-empty line as a minimal summary
        for ln in s.splitlines():
            if ln.strip() and not ln.strip().startswith('-') and not ln.strip().lower().startswith('##'):
                summary = ln.strip()
                break

    # Create a concise tailored resume docx (summary + bullets)
    os.makedirs("output/tailored", exist_ok=True)
    resume_out = f"output/tailored/{job_slug}_resume.docx"
    _save_docx_paragraphs(["SUMMARY:", summary, "", "HIGHLIGHTS:"] + [f"- {b}" for b in bullets] + ["", "KEYWORDS:", skills], resume_out)

    # Cover letter
    base_text = ""
    if os.path.exists(cfg.cover_letter_base_path):
        from docx import Document as D
        base_text = "\n".join(p.text for p in D(cfg.cover_letter_base_path).paragraphs)

    cl_text = llm.generate(
        COVER_LETTER_PROMPT.format(
            job_title=job.title or "",
            company=job.company or "",
            location=job.location or "",
            job_url=job.url or "",
            name=profile.name or "",
            email=profile.email or "",
            phone=profile.phone or "",
            base_text=base_text,
            job_text=job_text,
        ),
        max_tokens=700,
    )

    cl_out = f"output/tailored/{job_slug}_cover_letter.docx"
    _render_cover_letter_jinja(
        {
            "cover_letter_text": cl_text,
            "name": profile.name or "",
            "email": profile.email or "",
            "phone": profile.phone or "",
            "company": job.company or "Hiring Manager",
            "job_title": job.title or "the role",
        },
        cl_out,
    )
    return resume_out, cl_out
