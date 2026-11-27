"""Step 1: fetch listing + detail pages from TaladROD.

Selection: first N ads in the order shown on รถมาใหม่วันนี้
(SchDataJSON.cars). Cap is 100 per run by default.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

import requests

LISTING_URL = "https://www.taladrod.com/w40/isch/schc.aspx?fno:new"
DETAIL_URL = "https://www.taladrod.com/w40/iCar/CarDet.aspx?cid={cid}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "th-TH,th;q=0.9,en;q=0.8",
}

_SCH_JSON = re.compile(r"var SchDataJSON=(\{.*?\});", re.DOTALL)


def fetch(session: requests.Session, url: str, retries: int = 3, delay: float = 1.0) -> str:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            resp = session.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
        except Exception as exc:  # network / HTTP
            last = exc
            time.sleep(delay * (attempt + 1))
            continue
        if resp.status_code != requests.codes.ok:
            raise RuntimeError(
                f"unexpected HTTP status {resp.status_code} from {url}"
            )
        if not resp.content:
            raise RuntimeError(
                f"empty response body from {url} (HTTP {resp.status_code})"
            )
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text
    raise RuntimeError(f"failed after {retries} retries: {url}") from last


def parse_listing_cars(html: str) -> list[dict[str, Any]]:
    match = _SCH_JSON.search(html)
    if not match:
        raise ValueError("SchDataJSON not found on listing page")
    data = json.loads(match.group(1))
    cars = data.get("cars") or []
    return [c for c in cars if c.get("type") == "car" and c.get("cid")]


def listing_cars(session: requests.Session, delay: float) -> list[dict[str, Any]]:
    attempt = 1
    while True:
        html = fetch(session, LISTING_URL, delay=delay)
        try:
            cars = parse_listing_cars(html)
        except ValueError:
            if attempt == 3:
                raise
            time.sleep(delay * attempt)
            attempt += 1
            continue
        # fno:new currently returns the full set in one JSON payload.
        # If a later listing page uses pagination, walk it here until N cars.
        return cars


def detail_url(cid: str) -> str:
    return DETAIL_URL.format(cid=cid)


def fetch_detail(session: requests.Session, cid: str, delay: float) -> str:
    html = fetch(session, detail_url(cid), delay=delay)
    time.sleep(delay)
    return html
