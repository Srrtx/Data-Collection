# TaladROD used-car collector

Assignment pipeline for AI Data Engineer (Data Collection & Analysis).

## Selection

Source URL: https://www.taladrod.com/w40/isch/schc.aspx?fno:new

Take the **first 100 ads in listing order** (`SchDataJSON.cars` = รถมาใหม่วันนี้ as the site shows them). Cap is 100 per run.

## Pipeline

1. **Scrape** — fetch the listing page, then each `CarDet.aspx?cid=…`, with retries and delays for network/HTTP errors.
2. **Parse** — ad id, brand/model/year, price, mileage, source URL, every listing image URL.
3. **Classify** — infer vehicle type from brand/model/title rules mapped to TaladROD categories (เก๋ง/กระบะ/ตู้/สปอร์ต/ออฟโรด/อเนกประสงค์/รถหรู).
4. **Score** — calculate image quality from Laplacian variance (sharpness), brightness, and contrast, weighted 50%/25%/25%.
5. **Export** — archive each run under `output/YYYY-MM-DD/run_N/` with its own `ads.json` and `images/`. The root `output/ads.json` aggregates all run records.

## Run

```bash
pip install -r requirements.txt
python -m src.pipeline_classic --limit 100 --delay 1.0
```
Defaults: limit 100 ads and delay 1.0 second.

Each invocation creates the next numeric run ID for that date. Resume an interrupted run by passing its ID:

```bash
python -m src.pipeline_classic --limit 100 --delay 1.0 --run-id 2
```

Run data is stored in `data/YYYY-MM-DD/partial_N.jsonl`; images and the per-run archive are stored in `output/YYYY-MM-DD/run_N/`. The root `output/ads.json` is a JSON array containing one record per run, with image paths relative to `output/`. It is rebuilt from the per-run archives, so resuming a run updates that run's record instead of duplicating it. Existing flat-layout data and images are left untouched. The pipeline skips IDs already present in any partial file for that date, so each run stores only newly fetched ads. Run collectors sequentially for a date.

## OUTPUT
```json
[
  {
    "run_id": 1,
    "run_date": "2026-11-27",
    "source": "https://www.taladrod.com/w40/isch/schc.aspx?fno:new",
    "selection": "first 100 list by order (รถมาใหม่วันนี้)",
    "count": 1,
    "ads": [
      {
        "ad_id": "ad-1",
        "brand": "Example",
        "model": "Model",
        "year": 2020,
        "price": 350000,
        "mileage_km": 80000,
        "source_url": "https://example.test/ads/1",
        "vehicle_type": "car",
        "images": [
          {
            "path": "2026-11-27/run_1/images/ad-1_01.jpg",
            "source_url": "https://example.com/image.jpg",
            "method": "classic",
            "quality_score": 7.5
          }
        ]
      }
    ]
  },
  {
    "run_id": 2,
    "run_date": "2026-11-27",
    "source": "https://www.taladrod.com/w40/isch/schc.aspx?fno:new",
    "selection": "first 100 list by order (รถมาใหม่วันนี้)",
    "count": 0,
    "ads": []
  }
]
```
**Picture** 
  in folder output/run_n/images/