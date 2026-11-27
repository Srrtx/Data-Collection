"""Step 3: vehicle type from listing text (TaladROD Type1 labels).

The detail page does not print เก๋ง/กระบะ/ตู้. Rules use brand + model +
title, matching the site's own type dropdown.
"""

from __future__ import annotations

# More specific groups first.
_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        "รถกระบะ",
        (
            "hilux",
            "revo",
            "ranger",
            "d-max",
            "dmax",
            "triton",
            "navara",
            "bt-50",
            "bt50",
            "colorado",
            "amarok",
            "f-150",
            "f150",
            "truck",
            "กระบะ",
        ),
    ),
    (
        "รถตู้",
        (
            "hiace",
            "commuter",
            "alphard",
            "vellfire",
            "carnival",
            "starex",
            "urvan",
            "transit",
            "van",
            "รถตู้",
        ),
    ),
    (
        "รถสปอร์ต",
        (
            "supra",
            "mustang",
            "mx-5",
            "mx5",
            "86",
            "brz",
            "911",
            "cayman",
            "boxster",
            "z4",
            "tt ",
            "รถสปอร์ต",
        ),
    ),
    (
        "รถออฟโรด",
        (
            "land cruiser",
            "prado",
            "wrangler",
            "jimny",
            "defender",
            "g-class",
            "g class",
            "gwagen",
            "ออฟโรด",
        ),
    ),
    (
        "รถอเนกประสงค์",
        (
            "fortuner",
            "everest",
            "pajero",
            "glc",
            "gle",
            "gla",
            "glb",
            "gls",
            "glk",
            "x1",
            "x3",
            "x5",
            "x6",
            "x7",
            "q3",
            "q5",
            "q7",
            "q8",
            "tiguan",
            "sportage",
            "tucson",
            "captiva",
            "trailblazer",
            "cr-v",
            "crv",
            "hr-v",
            "hrv",
            "cx-3",
            "cx-5",
            "cx-8",
            "cx-9",
            "cx-30",
            "cx-60",
            "x-trail",
            "xtrail",
            "forester",
            "outlander",
            "rav4",
            "rush",
            "veloz",
            "xpander",
            "innova",
            "sienta",
            "xl7",
            "mu-x",
            "mux",
            "terios",
            "cross",
            "suv",
            "อเนกประสงค์",
        ),
    ),
    (
        "รถหรู",
        (
            "rolls",
            "bentley",
            "maybach",
            "ferrari",
            "lamborghini",
            "maserati",
            "porsche",
            "s-class",
            "s class",
            "7-series",
            "series 7",
        ),
    ),
]


def classify(ad: dict) -> str:
    blob = " ".join(
        [
            str(ad.get("brand") or ""),
            str(ad.get("model") or ""),
            str(ad.get("title") or ""),
            str(ad.get("body") or ""),
        ]
    ).lower()
    for label, keys in _RULES:
        if any(k in blob for k in keys):
            return label
    return None
