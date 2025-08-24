import os
from typing import Iterable
from config import cfg
from preferences import get_preferences
from utils.logger import get_logger
from storage.db import upsert_job, is_applied
from parsers.resume_parser import parse_resume
from generators.services.resume_tailor import ResumeTailor
from generators.services.cover_letter_service import CoverLetterService
from generators.services.fallback_service import FallbackService
from apply.applicant import apply
from storage.models import JobPost

from providers import indeed as indeed_p
from providers import wellfound as wellfound_p
from providers import internshala as internshala_p
from providers import linkedin as linkedin_p

logger = get_logger("main")

def _safe_part(s: str, limit: int = 12) -> str:
    part = ''.join(ch for ch in s if ch.isalnum() or ch in ('-', '_', ' ')).strip().replace(' ', '-')
    return part[:limit] if part else 'x'


def gather_jobs() -> list[JobPost]:
    prefs = get_preferences()
    locations = prefs.cities or ["India"]
    providers: list[tuple[str, callable]] = []
    if cfg.enable_indeed: providers.append(("indeed", indeed_p.search))
    if cfg.enable_wellfound: providers.append(("wellfound", wellfound_p.search))
    if cfg.enable_internshala: providers.append(("internshala", internshala_p.search))
    if cfg.enable_linkedin: providers.append(("linkedin", linkedin_p.search))

    results: list[JobPost] = []
    seen_ids: set[str] = set()
    for kw in prefs.keywords:
        for name, fn in providers:
            try:
                logger.info(f"Searching {name} for '{kw}'")
                for job in fn(kw, locations):
                    if job.job_id in seen_ids:
                        continue
                    seen_ids.add(job.job_id)
                    upsert_job(job.job_id, job.title, job.company, job.location, job.url, job.source)
                    results.append(job)
            except Exception as e:
                logger.warning(f"Provider {name} error: {e}")
    return results

def process_jobs(jobs: Iterable[JobPost], profile):
    processed: set[str] = set()
    for job in jobs:
        if job.job_id in processed:
            continue
        processed.add(job.job_id)
        if is_applied(job.job_id):
            continue
        # Make slug more unique and safe
        job_slug = f"{job.source}_{_safe_part(job.company, 10)}_{_safe_part(job.title, 14)}_{job.job_id[:8]}"
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join('output', 'tailored', job_slug)
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate resume and cover letter
        resume_out = os.path.join(output_dir, f'resume_{job_slug}.docx')
        cl_out = os.path.join(output_dir, f'cover_letter_{job_slug}.docx')
        
        try:
            # Create resume
            resume_tailor = ResumeTailor(profile, job)
            # Generate tailored content first
            tailored_data = resume_tailor.generate_tailored_content()
            # Create the resume with tailored content
            resume_tailor.create_tailored_resume(tailored_data, resume_out)
            
            # Create cover letter
            cl_service = CoverLetterService(profile, job)
            cl_service.generate_cover_letter(cl_out)
            
            logger.info(f"Tailored docs: {resume_out}, {cl_out}")
            
            # Attempt application (only if provider supports it here)
            applied = apply(job, resume_out, cl_out)
            logger.info(f"Applied={applied} to {job.title} @ {job.company} ({job.source}) -> {job.url}")
            
        except Exception as e:
            logger.error(f"Error processing job {job.job_id}: {e}")
            # Try fallback mechanism if available
            try:
                fallback = FallbackService(profile, job)
                fallback.create_basic_resume(resume_out)
                logger.warning(f"Used fallback resume for {job.job_id}")
                applied = apply(job, resume_out, None)
                logger.info(f"Applied with fallback={applied} to {job.title} @ {job.company}")
            except Exception as fallback_error:
                logger.error(f"Fallback also failed for {job.job_id}: {fallback_error}")

def main():
    profile = parse_resume(cfg.resume_path)
    logger.info(f"Parsed resume: name={profile.name} email={profile.email}")
    jobs = gather_jobs()
    # Filter for India / Remote globally is already handled by providers' location check
    process_jobs(jobs, profile)

if __name__ == "__main__":
    main()
