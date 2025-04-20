# scraper/constants.py

import random
import re

# ——————————————————————————
# 1) rotate your User‑Agents
# ——————————————————————————
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    # add more up‑to‑date strings as you like…
]

# ——————————————————————————
# 2) initial page headers
# ——————————————————————————
def get_headers_initial() -> dict:
    ua = random.choice(USER_AGENTS)
    return {
        "Host": "www.google.com",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;"
                  "q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Dest": "document",
        "Accept-Language": "en-US,en;q=0.9",
    }

# ——————————————————————————
# 3) AJAX/jobs request headers
# ——————————————————————————
def get_headers_jobs(user_agent: str) -> dict:
    return {
        "Host": "www.google.com",
        "Connection": "keep-alive",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": user_agent,
        "Referer": "https://www.google.com/",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Accept-Language": "en-US,en;q=0.9",
    }

# ——————————————————————————
# 4) extract the real async token
# ——————————————————————————
def extract_async_param(html: str) -> str:
    """
    Finds the `async` parameter that Google embeds in its search results page.
    """
    m = re.search(r'data-async-param="([^"]+)"', html) or \
        re.search(r'asyncParam\s*=\s*\'([^\']+)\'', html)
    if not m:
        raise RuntimeError("Could not find asyncParam in Google HTML")
    return m.group(1)
