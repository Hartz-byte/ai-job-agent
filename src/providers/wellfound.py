import requests, time
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

logger = get_logger("wellfound")
bucket = TokenBucket(cfg.requests_per_min)

BASE = "https://wellfound.com/jobs"  # formerly AngelList


def _fetch(q: str):
    bucket.consume()
    params = {"keyword": q}
    url = f"{BASE}?{urlencode(params)}"
    # Use Playwright to bypass basic bot protections
    html = fetch_html(url, wait_selector="[data-test='job-row'], a[href*='/jobs/']", timeout_ms=15000, referer="https://wellfound.com/")
    return html


def search(query: str, locations: list[str]) -> Iterable[JobPost]:
    try:
        html = _fetch(query)
    except Exception as e:
        logger.warning(f"Wellfound fetch error: {e}")
        return
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select("[data-test='job-row']") or soup.select("a[href*='/jobs/']")
    for c in cards[:25]:
        title = c.get("aria-label") or c.text.strip().split("\n")[0]
        company = c.get("data-company")
        url = c.get("href") or "#"
        if url.startswith("/"):
            url = "https://wellfound.com" + url
        loc_el = c.find(attrs={"data-test": "locations"})
        loc = normalize_location(loc_el.text.strip() if loc_el else "")
        desc = ""
        if not is_location_ok(loc, cfg.cities, cfg.countries, cfg.remote_ok, cfg.remote_global_ok):
            continue
        if not title or not company:
            # fallback parse
            pieces = [p.strip() for p in c.text.split("·") if p.strip()]
            if len(pieces) >= 2:
                title = pieces[0]
                company = pieces[1]
        jid = job_key(title or "unknown", company or "unknown", loc)
        yield JobPost(title=title or "Unknown", company=company or "Unknown", location=loc, description=desc, url=url, source="wellfound", job_id=jid)
        time.sleep(0.2)
