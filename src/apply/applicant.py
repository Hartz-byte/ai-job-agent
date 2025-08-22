from ..storage.models import JobPost
from ..storage.db import mark_applied
from ..config import cfg
from ..utils.logger import get_logger
from playwright.sync_api import sync_playwright
import time

logger = get_logger("apply")

def apply_linkedin_easy_apply(job: JobPost, resume_path: str, cover_letter_path: str) -> bool:
    if not cfg.apply_linkedin_easy_apply:
        return False
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="output/linkedin_state.json")
        page = context.new_page()
        page.goto(job.url, timeout=60000)
        page.wait_for_timeout(2000)
        # click Easy Apply
        if page.get_by_role("button", name="Easy Apply").count() == 0:
            logger.info("No Easy Apply button.")
            context.close(); browser.close()
            return False
        page.get_by_role("button", name="Easy Apply").first.click()
        page.wait_for_timeout(1500)

        # Upload resume if prompt exists
        if page.locator("input[type='file']").count():
            try:
                file_input = page.locator("input[type='file']").first
                file_input.set_input_files(resume_path)
            except Exception:
                pass

        # fill cover letter if textarea exists
        if page.locator("textarea").count():
            try:
                page.locator("textarea").first.fill(open_text(cover_letter_path))
            except Exception:
                pass

        # Iterate through modal steps (Next/Review/Submit)
        for _ in range(6):
            if page.get_by_role("button", name="Submit application").count():
                page.get_by_role("button", name="Submit application").click()
                page.wait_for_timeout(2000)
                logger.info("LinkedIn application submitted.")
                context.close(); browser.close()
                return True
            btn = page.get_by_role("button", name="Next").first if page.get_by_role("button", name="Next").count() else None
            if btn: btn.click()
            page.wait_for_timeout(1500)

        context.close(); browser.close()
        return False

def open_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def apply_internshala(job: JobPost, resume_path: str, cover_letter_path: str) -> bool:
    # Many Internshala applications require account flow; we can land on page and stop
    # for manual review OR automate basic flows similarly with Playwright after login.
    # Here we just open and return False to avoid TOS issues by default.
    return False

def apply(job: JobPost, resume_path: str, cover_letter_path: str) -> bool:
    if job.source == "linkedin":
        ok = apply_linkedin_easy_apply(job, resume_path, cover_letter_path)
    elif job.source == "internshala" and cfg.apply_internshala:
        ok = apply_internshala(job, resume_path, cover_letter_path)
    else:
        ok = False
    if ok:
        mark_applied(job.job_id, status="submitted", notes=f"via {job.source}")
    return ok
