from typing import Iterable
from config import cfg
from preferences import get_preferences
from utils.logger import get_logger
from storage.db import upsert_job, is_applied
from parsers.resume_parser import parse_resume
from generators.tailor import tailor_resume_and_cl
from apply.applicant import apply
from storage.models import JobPost

from providers import indeed as indeed_p
from providers import wellfound as wellfound_p
from providers import internshala as internshala_p
from providers import linkedin as linkedin_p

logger = get_logger("main")

def gather_jobs() -> list[JobPost]:
    prefs = get_preferences()
    locations = prefs.cities or ["India"]
    providers: list[tuple[str, callable]] = []
    if cfg.enable_indeed: providers.append(("indeed", indeed_p.search))
    if cfg.enable_wellfound: providers.append(("wellfound", wellfound_p.search))
    if cfg.enable_internshala: providers.append(("internshala", internshala_p.search))
    if cfg.enable_linkedin: providers.append(("linkedin", linkedin_p.search))

    results: list[JobPost] = []
    for kw in prefs.keywords:
        for name, fn in providers:
            try:
                logger.info(f"Searching {name} for '{kw}'")
                for job in fn(kw, locations):
                    upsert_job(job.job_id, job.title, job.company, job.location, job.url, job.source)
                    results.append(job)
            except Exception as e:
                logger.warning(f"Provider {name} error: {e}")
    return results

def process_jobs(jobs: Iterable[JobPost], profile):
    for job in jobs:
        if is_applied(job.job_id):
            continue
        job_slug = f"{job.source}_{job.job_id[:12]}"
        resume_out, cl_out = tailor_resume_and_cl(profile, job.description or job.title, job_slug)
        logger.info(f"Tailored docs: {resume_out}, {cl_out}")
        # Attempt application (only if provider supports it here)
        applied = apply(job, resume_out, cl_out)
        logger.info(f"Applied={applied} to {job.title} @ {job.company} ({job.source}) -> {job.url}")

def main():
    profile = parse_resume(cfg.resume_path)
    logger.info(f"Parsed resume: name={profile.name} email={profile.email}")
    jobs = gather_jobs()
    # Filter for India / Remote globally is already handled by providers' location check
    process_jobs(jobs, profile)

if __name__ == "__main__":
    main()
