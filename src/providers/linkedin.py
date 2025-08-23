import os
import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urlencode
from config import cfg
from storage.models import JobPost
from utils.dedupe import job_key
from utils.location_filter import is_location_ok, normalize_location
from utils.browser_fetch import fetch_html

# Configure logging (ensure directory exists)
os.makedirs('output/logs', exist_ok=True)
logging.basicConfig(
    filename='output/logs/linkedin.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

BASE_URL = "https://www.linkedin.com"
LOGIN_URL = f"{BASE_URL}/uas/login-submit"
JOB_SEARCH_URL = f"{BASE_URL}/jobs/search/"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
})

def linkedin_login():
    """
    Logs into LinkedIn using session cookies and credentials from cfg.
    """
    try:
        logging.info("Fetching login page...")
        login_page = session.get(f"{BASE_URL}/login")
        soup = BeautifulSoup(login_page.content, "html.parser")
        # Validate credentials
        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")
        if not email or not password:
            logging.warning("LINKEDIN_EMAIL or LINKEDIN_PASSWORD not set in environment.")
            return False

        # Extract CSRF token safely
        csrf_input = soup.find("input", {"name": "loginCsrfParam"})
        csrf = csrf_input["value"] if csrf_input and csrf_input.has_attr("value") else None
        if not csrf:
            logging.warning("Could not find LinkedIn login CSRF token.")
            return False

        payload = {
            "session_key": email,
            "session_password": password,
            "loginCsrfParam": csrf
        }

        logging.info("Attempting login...")
        response = session.post(LOGIN_URL, data=payload)

        if response.status_code == 200 and "feed" in response.url:
            logging.info("LinkedIn login successful.")
            return True
        else:
            logging.error("LinkedIn login failed.")
            return False
    except Exception as e:
        logging.error(f"LinkedIn login error: {e}")
        return False

def _parse_job_page(job_url: str) -> tuple[str, str, str, str]:
    """Fetch a LinkedIn job page and try to parse title, company, location, description.
    Uses Playwright via fetch_html to reduce 429/anti-bot issues.
    Returns (title, company, location, description). Fallbacks to safe defaults."""
    try:
        html = fetch_html(job_url, wait_selector="h1, h1.top-card-layout__title, h1.topcard__title", timeout_ms=15000, referer=BASE_URL)
        soup = BeautifulSoup(html, 'lxml')
        # Try multiple selectors as LinkedIn changes frequently
        title = (soup.select_one('h1') or soup.select_one('h1.top-card-layout__title') or soup.select_one('h1.topcard__title'))
        title = title.get_text(strip=True) if title else 'Unknown'
        company_el = (soup.select_one('a.topcard__org-name-link') or soup.select_one('span.topcard__flavor'))
        company = company_el.get_text(strip=True) if company_el else 'Unknown'
        loc_el = (soup.select_one('span.topcard__flavor--bullet') or soup.select_one('span.jobs-unified-top-card__bullet'))
        location = normalize_location(loc_el.get_text(strip=True) if loc_el else 'Remote')
        desc_el = soup.select_one('div.show-more-less-html__markup') or soup.find('section', {'class':'description'})
        description = desc_el.get_text(separator=' ', strip=True)[:800] if desc_el else ''
        return title, company, location, description
    except Exception as e:
        logging.warning(f"Parse job page failed for {job_url}: {e}")
        return 'Unknown', 'Unknown', 'Remote', ''


def search(query: str, locations: list[str]):
    """Compatibility wrapper to return iterable of JobPost for given query/locations.
    Uses requests-based scraping. Requires valid LinkedIn credentials in environment
    (LINKEDIN_EMAIL, LINKEDIN_PASSWORD)."""
    # Attempt login once (best-effort)
    try:
        linkedin_login()
    except Exception:
        pass

    locs = locations or ["India"]
    for loc in locs:
        try:
            items = search_jobs(keywords=query, location=loc, remote=cfg.remote_ok or cfg.remote_global_ok)
        except Exception as e:
            logging.error(f"LinkedIn search failed for location '{loc}': {e}")
            continue

        cap = 30  # limit per location
        for item in items[:cap]:
            try:
                title = item.get("title") or "Unknown"
                company = item.get("company") or "Unknown"
                location = item.get("location") or normalize_location(loc)
                description = ""
                if not is_location_ok(location, cfg.cities, cfg.countries, cfg.remote_ok, cfg.remote_global_ok):
                    continue
                jid = job_key(title, company, location)
                yield JobPost(
                    title=title,
                    company=company,
                    location=location,
                    description=description,
                    url=item.get("url", "#"),
                    source='linkedin',
                    job_id=jid,
                )
            except Exception as e:
                logging.warning(f"Failed to parse or yield job '{item}': {e}")


def search_jobs(keywords, location="India", experience="Entry level", remote=True):
    """
    Searches LinkedIn jobs using the public jobs-guest endpoint with pagination.
    Returns a list of job URLs.
    """
    try:
        logging.info(f"Searching LinkedIn jobs for keywords: {keywords}, location: {location}")
        results: list[dict] = []
        start = 0
        per_page_empty = 0
        while start <= 150 and len(results) < 60:  # up to ~6 pages or 60 results cap
            params = {
                "keywords": keywords,
                "location": location,
                "f_E": "2",  # Entry-level
                "f_WT": "2" if remote else "",  # Remote filter
                "sortBy": "R",
                "start": str(start),
            }
            url = f"{BASE_URL}/jobs-guest/jobs/api/seeMoreJobPostings/search?{urlencode(params)}"
            # Basic backoff on 429
            attempts = 0
            backoff = 1.0
            r = None
            while attempts < 3:
                r = session.get(url, timeout=15)
                if r.status_code == 429:
                    logging.info(f"LinkedIn guest page {start} returned 429, backing off {backoff:.1f}s (attempt {attempts+1}/3)")
                    time.sleep(backoff)
                    backoff *= 2
                    attempts += 1
                    continue
                break
            if not r or r.status_code != 200:
                code = r.status_code if r else 'n/a'
                logging.info(f"LinkedIn guest page {start} returned {code}")
                break
            html = r.text
            soup = BeautifulSoup(html, "lxml")
            cards = soup.select(".base-search-card, .job-search-card")
            page_items = []
            for card in cards:
                a = card.select_one("a.base-card__full-link, a[data-tracking-control-name]")
                href = a.get("href") if a else None
                if not href:
                    continue
                title_el = card.select_one("h3.base-search-card__title, .job-card-list__title")
                title = title_el.get_text(strip=True) if title_el else None
                comp_el = card.select_one("h4.base-search-card__subtitle a, h4.base-search-card__subtitle, .job-card-container__company-name")
                company = comp_el.get_text(strip=True) if comp_el else None
                loc_el = card.select_one(".job-search-card__location, .base-search-card__metadata span")
                loc_text = loc_el.get_text(strip=True) if loc_el else None
                page_items.append({
                    "url": href,
                    "title": title,
                    "company": company,
                    "location": normalize_location(loc_text) if loc_text else normalize_location(location),
                })
            if not page_items:
                per_page_empty += 1
                if per_page_empty >= 2:
                    break
            else:
                per_page_empty = 0
                results.extend(page_items)
            start += 25
            time.sleep(0.4)
        # De-duplicate by URL
        deduped = []
        seen = set()
        for item in results:
            if item["url"] in seen:
                continue
            seen.add(item["url"])
            deduped.append(item)
        logging.info(f"Found {len(deduped)} jobs on LinkedIn.")
        return deduped
    except Exception as e:
        logging.error(f"Error searching jobs: {str(e)}")
        return []


def apply_job(job_url, resume_path, cover_letter_path):
    """
    Placeholder for applying to a job (LinkedIn Easy Apply requires automation).
    Later, we can use Selenium for Easy Apply.
    """
    try:
        logging.info(f"Applying to job: {job_url}")
        # TODO: Implement Selenium-based Easy Apply feature
        time.sleep(2)
        logging.info("Applied successfully (simulated).")
        return True
    except Exception as e:
        logging.error(f"Error applying job: {str(e)}")
        return False


if __name__ == "__main__":
    if linkedin_login():
        keywords = "AI Engineer"
        job_urls = search_jobs(keywords=keywords, location="India", remote=True)
        print(f"Found {len(job_urls)} jobs for {keywords}")

        # Simulate applying to first 2 jobs
        for job_url in job_urls[:2]:
            apply_job(job_url, cfg.resume_path, cfg.cover_letter_base_path)
