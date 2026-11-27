"""Step 2: parse brand/model/year, price, mileage, source URL, image URLs."""

from __future__ import annotations

import re #regax
from typing import Any

from .scrape import detail_url

_MILEAGE = re.compile(r"เลขไมล์\s*([\d,]+)\s*กม")
_IMG_PREFIX = re.compile(r"(https://imgc2\.taladrod\.com/c/cidx/\d+/\d+/\d+)_\d+")


def _int_or_none(value: str | None) -> int | None:
    if value is None:
        return None
    digits = re.sub(r"[^\d]", "", str(value))
    return int(digits) if digits else None


def image_prefix(listing_img: str) -> str | None:
    match = _IMG_PREFIX.search(listing_img or "")
    return match.group(1) if match else None


def parse_image_urls(detail_html: str, listing_img: str) -> list[str]:
    prefix = image_prefix(listing_img)
    if not prefix:
        return []
    # `_1.jpg` matches; `_1T3.jpg` (thumbs) does not.
    nums = {int(n) for n in re.findall(re.escape(prefix) + r"_(\d+)\.jpg", detail_html)}
    if not nums:
        return [f"{prefix}_1.jpg"]
    return [f"{prefix}_{n}.jpg" for n in sorted(nums)]


def parse_ad(car: dict[str, Any], detail_html: str) -> dict[str, Any]:
    cid = str(car["cid"])
    mileage = None
    match = _MILEAGE.search(detail_html)
    if match:
        mileage = _int_or_none(match.group(1))

    title = (car.get("namemmt") or "").strip()
    brand = (car.get("amake") or "").strip()
    model = (car.get("amodel") or car.get("model") or "").strip()
    tokens = title.split()
    if not brand and tokens:
        brand = tokens[0]
    if not model and len(tokens) > 1:
        model = tokens[1]

    return {
        "ad_id": cid,
        "brand": brand,
        "model": model,
        "year": _int_or_none(car.get("yr4")),
        "price": _int_or_none(car.get("prc")),
        "mileage_km": mileage,
        "title": title,
        "body": (car.get("abody") or "").strip(),
        "source_url": detail_url(cid),
        "image_urls": parse_image_urls(detail_html, car.get("img") or ""),
    }
