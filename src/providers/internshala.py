import time
from bs4 import BeautifulSoup
from typing import Iterable
from storage.models import JobPost
from utils.dedupe import job_key
from utils.location_filter import is_location_ok, normalize_location
from config import cfg
from utils.rate_limit import TokenBucket
from utils.logger import get_logger
from utils.browser_fetch import fetch_html

logger = get_logger("internshala")
bucket = TokenBucket(cfg.requests_per_min)

BASE = "https://internshala.com/internships/machine-learning-internship"

def _fetch():
    bucket.consume()
    # Wait for internship cards to be present
    html = fetch_html(BASE, wait_selector="div.individual_internship", timeout_ms=15000, referer="https://internshala.com/")
    return html

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
        # Title: prefer explicit job-title anchor
        title_el = c.select_one("a.job-title-href, h3.job-internship-name a, div.heading_4_5, a.view_detail_button, a[href*='/internship/detail/']")
        title = title_el.get_text(strip=True) if title_el else "Internship"
        # Company: include p.company-name as per sample DOM
        company_el = c.select_one("p.company-name, .company .company_name, .company_and_premium .company-name, div.heading_6 span, a.link_display_like_text, .company_name a, .company_and_premium a")
        company = company_el.get_text(strip=True) if company_el else "Unknown"
        # Location: broaden selector fallbacks
        loc_el = c.select_one("a.location_link, .locations span, .other_detail_item .link_display_like_text, .location_link span")
        loc = normalize_location(loc_el.get_text(strip=True) if loc_el else "Remote")
        desc_el = c.select_one(".internship_overview, .internship_meta, .internship_details") or c
        desc = desc_el.get_text(separator=' ', strip=True)[:400]
        url_el = c.select_one("a.job-title-href, a.view_detail_button, a[href*='/internship/detail/']")
        url = (url_el["href"] if url_el and url_el.has_attr("href") else "#")
        if url.startswith("/"):
            url = "https://internshala.com" + url
        # Detail page fallback if company still Unknown or title generic
        if (not company or company == "Unknown" or company == "") and url and url != "#":
            try:
                detail_html = fetch_html(url, wait_selector="div.company, .heading_6, .internship_meta", timeout_ms=12000, referer=BASE)
                ds = BeautifulSoup(detail_html, "lxml")
                d_title = ds.select_one("h1, h2, h3.job-internship-name, .profile_on_detail_page")
                if d_title:
                    title = d_title.get_text(strip=True) or title
                d_company = ds.select_one("p.company-name, .company .heading_6, .company .link_display_like_text, .employer_name, .company_name")
                if d_company:
                    company = d_company.get_text(strip=True) or company
                d_loc = ds.select_one(".location_link, .other_detail_item .link_display_like_text, .locations span")
                if d_loc:
                    loc = normalize_location(d_loc.get_text(strip=True)) or loc
            except Exception as e:
                logger.debug(f"Internshala detail fetch failed for {url}: {e}")
        if not is_location_ok(loc, cfg.cities, cfg.countries, cfg.remote_ok, cfg.remote_global_ok):
            continue
        jid = job_key(title, company, loc)
        yield JobPost(title=title, company=company, location=loc, description=desc, url=url, source="internshala", job_id=jid)
        time.sleep(0.2)
