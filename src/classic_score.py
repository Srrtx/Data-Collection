"""Step 4: local image quality score (0-10).

Classical CV: Laplacian variance (blur), brightness, contrast.
Chosen so the batch runs on CPU with no external vision API.
"""

from __future__ import annotations

import math
from pathlib import Path
import cv2
import numpy as np
import requests

from .scrape import HEADERS


def download_image(session: requests.Session, url: str, dest: Path, delay: float) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        resp = session.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        return dest.stat().st_size > 0
    except Exception:
        return False

# Ruturm 0.0-10.0 (Gray scal-> Laplacian(shrapness)-> brightness 128lv. from grayscal-> contrast(Mean) ->Score(shrapness50/brightness25/contrast25)
def score_image(path: Path) -> float:
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR) #read images
    if img is None:
        return 0.0
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #Gray scal
    sharp = float(cv2.Laplacian(gray, cv2.CV_64F).var()) # use Laplacian (shrapness)
    sharp_s = min(10.0, max(0.0, math.log10(sharp + 1.0) / math.log10(1500.0) * 10.0)) # score shrapness
    mean = float(gray.mean()) #use Mean
    bright_s = 10.0 * (1.0 - abs(mean - 128.0) / 128.0)
    contrast_s = min(10.0, float(gray.std()) / 8.0)
    score = 0.50 * sharp_s + 0.25 * bright_s + 0.25 * contrast_s
    return round(float(score), 1)
