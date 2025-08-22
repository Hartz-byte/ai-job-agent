import requests, time
from bs4 import BeautifulSoup
from typing import Iterable
from ..storage.models import JobPost
from ..utils.dedupe import job_key
from ..utils.location_filter import is_location_ok, normalize_location
from ..config import cfg
from ..utils.rate_limit import TokenBucket
from ..utils.logger import get_logger

logger = get_logger("internshala")
bucket = TokenBucket(cfg.requests_per_min)

BASE = "https://internshala.com/internships/machine-learning-internship"

def _fetch():
    bucket.consume()
    r = requests.get(BASE, timeout=20, headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    return r.text

def search(query: str, locations: list[str]) -> Iterable[JobPost]:
    # Internshala is internship-centric; we ignore query and parse main ml page
    try:
        html = _fetch()
    except Exception as e:
        logger.warning(f"Internshala fetch error: {e}")
        return
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select("div.individual_internship")
    for c in cards[:30]:
        title = (c.select_one("div.heading_4_5") or {}).text.strip() if c.select_one("div.heading_4_5") else "Internship"
        company = (c.select_one("div.heading_6 span") or {}).text.strip() if c.select_one("div.heading_6 span") else "Unknown"
        loc = normalize_location((c.select_one("a.location_link") or {}).text.strip() if c.select_one("a.location_link") else "Remote")
        desc = (c.select_one(".internship_overview") or c).text.strip()[:400]
        url_el = c.select_one("a.view_detail_button")
        url = "https://internshala.com" + (url_el["href"] if url_el and url_el.has_attr("href") else "#")
        if not is_location_ok(loc, cfg.cities, cfg.countries, cfg.remote_ok, cfg.remote_global_ok):
            continue
        jid = job_key(title, company, loc)
        yield JobPost(title=title, company=company, location=loc, description=desc, url=url, source="internshala", job_id=jid)
        time.sleep(0.2)
