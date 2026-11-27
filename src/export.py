"""Step 5: write combined JSON."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .scrape import LISTING_URL


def next_run_id(data_dir: Path, output_date_dir: Path) -> int:
    run_ids = []
    if data_dir.exists():
        run_ids.extend(
            int(path.stem.removeprefix("partial_"))
            for path in data_dir.glob("partial_*.jsonl")
            if path.stem.removeprefix("partial_").isdigit()
        )
    if output_date_dir.exists():
        run_ids.extend(
            int(path.name.removeprefix("run_"))
            for path in output_date_dir.glob("run_*")
            if path.is_dir() and path.name.removeprefix("run_").isdigit()
        )
    return max(run_ids, default=0) + 1


def _run_key(payload: dict[str, Any]) -> tuple[str, int]:
    return str(payload["run_date"]), int(payload["run_id"])


def _payload_for_root(
    payload: dict[str, Any], archive_path: Path, output_root: Path
) -> dict[str, Any]:
    root_payload = copy.deepcopy(payload)
    image_prefix = archive_path.parent.relative_to(output_root)
    for ad in root_payload["ads"]:
        for image in ad.get("images", []):
            image["path"] = (image_prefix / image["path"]).as_posix()
    return root_payload


def export_ads(
    ads: list[dict[str, Any]],
    archive_path: Path,
    limit: int,
    run_id: int,
    mirror_path: Path,
) -> None:
    payload = {
        "run_id": run_id,
        "run_date": archive_path.parent.parent.name,
        "source": LISTING_URL,
        "selection": f"first {limit} list by order (รถมาใหม่วันนี้)",
        "count": len(ads),
        "ads": ads,
    }
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    runs: dict[tuple[str, int], dict[str, Any]] = {}
    if mirror_path.exists():
        existing = json.loads(mirror_path.read_text(encoding="utf-8"))
        existing_runs = existing if isinstance(existing, list) else [existing]
        for existing_run in existing_runs:
            runs[_run_key(existing_run)] = existing_run

    for run_archive in mirror_path.parent.glob("*/run_*/ads.json"):
        archived_payload = json.loads(run_archive.read_text(encoding="utf-8"))
        root_payload = _payload_for_root(
            archived_payload, run_archive, mirror_path.parent
        )
        runs[_run_key(root_payload)] = root_payload

    run_list = [runs[key] for key in sorted(runs)]
    mirror_path.parent.mkdir(parents=True, exist_ok=True)
    mirror_path.write_text(
        json.dumps(run_list, ensure_ascii=False, indent=2), encoding="utf-8"
    )
