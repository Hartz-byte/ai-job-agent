import time
from bs4 import BeautifulSoup
from typing import Iterable
from storage.models import JobPost
from utils.dedupe import job_key
from utils.location_filter import is_location_ok, normalize_location
from config import cfg
from utils.rate_limit import TokenBucket
from utils.logger import get_logger
from urllib.parse import urlencode
from utils.browser_fetch import fetch_html

logger = get_logger("indeed")
bucket = TokenBucket(cfg.requests_per_min)

BASE = "https://in.indeed.com/jobs"


def _fetch(q: str, start: int = 0):
    bucket.consume()
    params = {"q": q, "start": start}
    url = f"{BASE}?{urlencode(params)}"
    # Use Playwright to bypass basic bot protections
    html = fetch_html(url, wait_selector="div.job_seen_beacon", timeout_ms=15000, referer="https://in.indeed.com/")
    return html


def search(query: str, locations: list[str]) -> Iterable[JobPost]:
    for start in range(0, 30, 10):  # first 3 pages
        try:
            html = _fetch(query, start)
        except Exception as e:
            logger.warning(f"Indeed fetch error: {e}")
            break
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select("div.job_seen_beacon")
        for c in cards:
            a = c.select_one("h2 a")
            title = (a.get("aria-label") if a and a.has_attr("aria-label") else None) or (a.get("title") if a and a.has_attr("title") else None) or (a.get_text(strip=True) if a else None) or "Unknown"
            url = "https://in.indeed.com" + (a["href"] if a and a.has_attr("href") else "#")
            comp_el = c.select_one(".company_name, span.companyName, .jobCardShelfContainer .companyName")
            company = comp_el.get_text(strip=True) if comp_el else "Unknown"
            loc_el = c.select_one(".company_location, .companyLocation, .metadataContainer .companyLocation")
            loc = normalize_location(loc_el.get_text(strip=True) if loc_el else "")
            desc = (c.select_one(".job-snippet") or c.select_one(".resultContent")).text.strip() if c.select_one(".job-snippet") or c.select_one(".resultContent") else ""
            if not is_location_ok(loc, cfg.cities, cfg.countries, cfg.remote_ok, cfg.remote_global_ok):
                continue
            jid = job_key(title, company, loc)
            yield JobPost(title=title, company=company, location=loc, description=desc, url=url, source="indeed", job_id=jid)
        time.sleep(1)
