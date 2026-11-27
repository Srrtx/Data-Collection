"""Run scrape → parse → classify → score → export."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.classify import classify
from src.export import export_ads, next_run_id
from src.parse import parse_ad
from src.scrape import fetch_detail, listing_cars
from src.classic_score import download_image, score_image

OUT = ROOT / "output"


def _load_done_ids(data_dir: Path) -> set[str]:
    done = set()
    for partial in data_dir.glob("partial_*.jsonl"):
        for line in partial.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(str(json.loads(line)["ad_id"]))
    return done


def _append_partial(ad: dict, done: set[str], partial: Path) -> bool:
    ad_id = str(ad["ad_id"])
    if ad_id in done:
        return False
    partial.parent.mkdir(parents=True, exist_ok=True)
    with partial.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(ad, ensure_ascii=False) + "\n")
    # ponytail: per-date cache assumes sequential runs; add locking if concurrency is needed.
    done.add(ad_id)
    return True


def collect_images(
    session: requests.Session, ad: dict, delay: float, images_dir: Path
) -> list[dict]:
    rows = []
    for i, url in enumerate(ad["image_urls"], start=1):
        dest = images_dir / f"{ad['ad_id']}_{i:02d}.jpg"
        ok = download_image(session, url, dest, delay)
        time.sleep(delay)
        if not ok:
            continue
        rows.append(
            {
                "path": dest.relative_to(images_dir.parent).as_posix(),
                "source_url": url,
                "method" : 'classic',
                "quality_score": score_image(dest),
            }
        )
    return rows


def run(limit: int, delay: float, run_id: int | None = None) -> Path:
    run_at = datetime.now().astimezone()
    run_date = run_at.date().isoformat()
    data_dir = ROOT / "data" / run_date
    output_date_dir = OUT / run_date
    if run_id is not None and run_id < 1:
        raise ValueError("run_id must be a positive integer")
    if run_id is None:
        run_id = next_run_id(data_dir, output_date_dir)
    partial = data_dir / f"partial_{run_id}.jsonl"
    run_dir = output_date_dir / f"run_{run_id}"
    images_dir = run_dir / "images"
    archive = run_dir / "ads.json"
    mirror = OUT / "ads.json"

    partial.parent.mkdir(parents=True, exist_ok=True)
    partial.touch(exist_ok=True)
    print(f"starting run {run_id} for {run_date}", flush=True)
    session = requests.Session()
    cars = listing_cars(session, delay)[:limit]
    print(f"listing cars available, taking {len(cars)} (limit={limit})", flush=True)

    done = _load_done_ids(data_dir)
    ads: list[dict] = []
    if partial.exists():
        for line in partial.read_text(encoding="utf-8").splitlines():
            if line.strip():
                ads.append(json.loads(line))

    for i, car in enumerate(cars, start=1):
        cid = str(car["cid"])
        if cid in done:
            print(f"[{i}/{len(cars)}] skip {cid} (cached)", flush=True)
            continue
        print(f"[{i}/{len(cars)}] {cid} {car.get('amake') or ''} {car.get('amodel') or car.get('model') or ''}", flush=True)
        try:
            html = fetch_detail(session, cid, delay)
            ad = parse_ad(car, html)
            ad["vehicle_type"] = classify(ad)
            ad["images"] = collect_images(session, ad, delay, images_dir)
            ad.pop("image_urls", None)
            ad.pop("title", None)
            ad.pop("body", None)
        except Exception as exc:
            print(f"  error {cid}: {exc}", flush=True)
            continue
        if not _append_partial(ad, done, partial):
            continue
        ads.append(ad)

    wanted = {str(c["cid"]) for c in cars}
    ads = [a for a in ads if a["ad_id"] in wanted]
    export_ads(ads, archive, limit, run_id, mirror)
    print(
        f"wrote {archive} ({len(ads)} ads, images in {images_dir}; aggregate {mirror})",
        flush=True,
    )
    return mirror


def main() -> None:
    parser = argparse.ArgumentParser(description="TaladROD used-car collector")
    parser.add_argument("--limit", type=int, default=100, help="max ads per run (assignment cap: 100)")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    parser.add_argument("--run-id", type=int, help="resume this run ID instead of starting a new run")
    args = parser.parse_args()
    if args.run_id is not None and args.run_id < 1:
        parser.error("--run-id must be a positive integer")
    run(min(args.limit, 100), args.delay, args.run_id)


if __name__ == "__main__":
    main()
