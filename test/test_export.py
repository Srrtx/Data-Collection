import json
import tempfile
import unittest
from pathlib import Path

from src.export import export_ads, next_run_id


class ExportTests(unittest.TestCase):
    def test_root_ads_file_aggregates_runs_and_updates_resumed_record(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data_date_dir = root / "data" / "2026-11-27"
            output_date_dir = root / "output" / "2026-11-27"
            mirror_path = root / "output" / "ads.json"
            ad = {"ad_id": "car-old", "images": [{"path": "images/car.jpg"}]}
            resumed_ad = {
                "ad_id": "car-updated",
                "images": [{"path": "images/car-updated.jpg"}],
            }
            second_ad = {"ad_id": "car-2", "images": [{"path": "images/car-2.jpg"}]}

            first_id = next_run_id(data_date_dir, output_date_dir)
            first_archive = output_date_dir / "run_1" / "ads.json"
            export_ads([ad], first_archive, 100, first_id, mirror_path)
            export_ads([resumed_ad], first_archive, 100, first_id, mirror_path)
            (data_date_dir / "partial_1.jsonl").parent.mkdir(parents=True)
            (data_date_dir / "partial_1.jsonl").touch()

            second_id = next_run_id(data_date_dir, output_date_dir)
            second_archive = output_date_dir / "run_2" / "ads.json"
            export_ads([second_ad], second_archive, 100, second_id, mirror_path)
            next_date_id = next_run_id(
                root / "data" / "2026-11-28",
                root / "output" / "2026-11-28",
            )

            first_payload = json.loads(first_archive.read_text(encoding="utf-8"))
            runs = json.loads(mirror_path.read_text(encoding="utf-8"))
            second_payload = json.loads(second_archive.read_text(encoding="utf-8"))

        self.assertEqual(first_id, 1)
        self.assertEqual(second_id, 2)
        self.assertEqual(next_date_id, 1)
        self.assertEqual(first_payload["run_date"], "2026-11-27")
        self.assertEqual(first_payload["ads"][0]["images"][0]["path"], "images/car-updated.jpg")
        self.assertEqual([run["run_id"] for run in runs], [1, 2])
        self.assertEqual(runs[0]["count"], 1)
        self.assertEqual(runs[0]["ads"][0]["ad_id"], "car-updated")
        self.assertEqual(
            runs[0]["ads"][0]["images"][0]["path"],
            "2026-11-27/run_1/images/car-updated.jpg",
        )
        self.assertEqual(runs[1]["ads"][0]["ad_id"], "car-2")
        self.assertEqual(
            runs[1]["ads"][0]["images"][0]["path"],
            "2026-11-27/run_2/images/car-2.jpg",
        )
        self.assertEqual(second_payload["ads"][0]["images"][0]["path"], "images/car-2.jpg")
        self.assertEqual(ad["images"][0]["path"], "images/car.jpg")


if __name__ == "__main__":
    unittest.main()
