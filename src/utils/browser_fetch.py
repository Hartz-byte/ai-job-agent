from playwright.sync_api import sync_playwright
from typing import Optional


def fetch_html(url: str, wait_selector: Optional[str] = None, timeout_ms: int = 15000, referer: Optional[str] = None, short_wait_ms: int = 600) -> str:
    """
    Fetch page HTML using Playwright Chromium in headless mode.
    - wait_selector: optional CSS selector to wait for before returning content.
    - timeout_ms: maximum time to wait for navigation/selector.
    - referer: optional referer header to set for initial navigation.
    - short_wait_ms: when selector wait fails or not provided, wait briefly before reading content.
    Returns the full page content as a string.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="UTC",
        )
        page = context.new_page()
        headers = {"Accept-Language": "en-US,en;q=0.9"}
        if referer:
            headers["Referer"] = referer
        page.set_extra_http_headers(headers)
        page.goto(url, timeout=timeout_ms)
        if wait_selector:
            try:
                page.wait_for_selector(wait_selector, timeout=timeout_ms)
            except Exception:
                page.wait_for_timeout(short_wait_ms)
        else:
            page.wait_for_timeout(short_wait_ms)
        html = page.content()
        context.close()
        browser.close()
        return html
