from typing import Iterable
from playwright.sync_api import sync_playwright
import os
from ..storage.models import JobPost
from ..utils.dedupe import job_key
from ..utils.location_filter import is_location_ok, normalize_location
from ..config import cfg
from ..utils.logger import get_logger
import time, urllib.parse

logger = get_logger("linkedin")

LI_SEARCH = "https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}&f_AL=true"  # f_AL=true => Easy Apply

def search(query: str, locations: list[str]) -> Iterable[JobPost]:
    """Search LinkedIn jobs. If no saved session exists, opens an interactive window for manual login once, then saves session.

    You can force interactive login by setting environment variable LI_INTERACTIVE=1.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.linkedin.com/login")
        input("Log in manually and press Enter here...")
        context.storage_state(path="output/linkedin_state.json")
        print("✅ LinkedIn login state saved.")

    with sync_playwright() as p:
        force_interactive = os.getenv("LI_INTERACTIVE", "0") == "1"
        has_state = _has_state() and not force_interactive
        # Use GUI for first-time login, headless afterwards
        browser = p.chromium.launch(
            headless=has_state and not force_interactive,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"],
        )
        context = browser.new_context(storage_state="output/linkedin_state.json" if has_state else None)
        page = context.new_page()

        # If no session or forced interactive, allow user to login once
        if not has_state:
            try:
                logger.info("No LinkedIn session. Opening login page for manual sign-in...")
                page.goto("https://www.linkedin.com/login", timeout=60000)
                # Wait up to ~90s for user to login (page will typically redirect to /feed after login)
                for _ in range(18):
                    page.wait_for_timeout(5000)
                    if "linkedin.com/feed" in page.url or page.locator("nav.global-nav").count() > 0:
                        break
                # Persist session for future runs
                context.storage_state(path="output/linkedin_state.json")
                logger.info("LinkedIn session saved to output/linkedin_state.json")
            except Exception as e:
                logger.warning(f"Login flow encountered an issue: {e}")

        for loc in (locations or ["India"]):
            url = LI_SEARCH.format(
                keywords=urllib.parse.quote(query),
                location=urllib.parse.quote(loc)
            )
            logger.info(f"LinkedIn search {url}")
            page.goto(url, timeout=60000)
            # Allow content to load and scroll to trigger lazy loading
            page.wait_for_timeout(4000)
            # Wait for job list if present
            try:
                page.wait_for_selector("ul.scaffold-layout__list-container li a.base-card__full-link", timeout=15000)
            except Exception:
                pass
            try:
                for _ in range(4):
                    page.mouse.wheel(0, 2000)
                    page.wait_for_timeout(1200)
            except Exception:
                pass
            # Extract job cards
            cards = page.query_selector_all("ul.scaffold-layout__list-container li a.base-card__full-link")
            if not cards:
                logger.warning("No LinkedIn job cards found on the page. UI/layout may have changed or login required.")
            for a in cards[:25]:
                href = a.get_attribute("href") or "#"
                title_el = a.query_selector("span.sr-only")
                title = (title_el.inner_text().strip() if title_el else a.inner_text().strip()).split(" - ")[0]
                # Visit to fetch company & location
                page.goto(href, timeout=60000)
                page.wait_for_timeout(1500)
                company = page.locator("a.topcard__org-name-link, span.topcard__flavor").first.inner_text(timeout=2000) if page.locator("a.topcard__org-name-link, span.topcard__flavor").count() else "Unknown"
                loc = page.locator("span.topcard__flavor--bullet").first.inner_text(timeout=2000) if page.locator("span.topcard__flavor--bullet").count() else "Remote"
                loc = normalize_location(loc)
                desc = page.locator("div.show-more-less-html__markup").first.inner_text(timeout=2000)[:600] if page.locator("div.show-more-less-html__markup").count() else ""
                if not is_location_ok(loc, cfg.cities, cfg.countries, cfg.remote_ok, cfg.remote_global_ok):
                    continue
                jid = job_key(title, company, loc)
                yield JobPost(title=title, company=company, location=loc, description=desc, url=href, source="linkedin", job_id=jid)
                time.sleep(0.2)
        # Save session in case cookies updated
        try:
            context.storage_state(path="output/linkedin_state.json")
        except Exception:
            pass
        context.close()
        browser.close()

def _has_state() -> bool:
    import os
    return os.path.exists("output/linkedin_state.json")
