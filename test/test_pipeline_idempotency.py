import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from src import pipeline_classic
from quarantine import pipeline_hybrid


class PartialIdempotencyTests(unittest.TestCase):
    def test_retry_does_not_append_saved_ad_twice(self):
        with tempfile.TemporaryDirectory() as folder:
            partial = Path(folder) / "partial.jsonl"
            ad = {"ad_id": "123"}
            self.assertTrue(pipeline_hybrid._append_partial(ad, set(), partial))
            self.assertFalse(
                pipeline_hybrid._append_partial(ad, pipeline_hybrid._load_done_ids(partial), partial)
            )
            self.assertEqual(len(partial.read_text(encoding="utf-8").splitlines()), 1)

    def test_explicit_run_id_resumes_its_partial_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = root / "output"
            run_date = "2026-11-27"
            partial = root / "data" / run_date / "partial_7.jsonl"
            partial.parent.mkdir(parents=True)
            ad = {"ad_id": "123", "images": []}
            partial.write_text('{"ad_id":"123","images":[]}\n', encoding="utf-8")

            with patch.object(pipeline_classic, "ROOT", root):
                with patch.object(pipeline_classic, "OUT", output):
                    with patch.object(pipeline_classic, "datetime") as clock:
                        clock.now.return_value = datetime(
                            2026, 11, 27, tzinfo=timezone.utc
                        )
                        with patch.object(
                            pipeline_classic,
                            "listing_cars",
                            return_value=[{"cid": "123"}],
                        ):
                            with patch.object(pipeline_classic, "fetch_detail") as fetch:
                                with patch.object(
                                    pipeline_classic, "export_ads"
                                ) as export:
                                    result = pipeline_classic.run(100, 0, 7)

        fetch.assert_not_called()
        export.assert_called_once_with(
            [ad],
            output / run_date / "run_7" / "ads.json",
            100,
            7,
            output / "ads.json",
        )
        self.assertEqual(result, output / "ads.json")

    def test_new_run_skips_ad_cached_by_an_earlier_run(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = root / "output"
            run_date = "2026-11-27"
            data_dir = root / "data" / run_date
            data_dir.mkdir(parents=True)
            (data_dir / "partial_1.jsonl").write_text(
                '{"ad_id":"123","images":[]}\n', encoding="utf-8"
            )
            current_partial = data_dir / "partial_2.jsonl"

            with patch.object(pipeline_classic, "ROOT", root):
                with patch.object(pipeline_classic, "OUT", output):
                    with patch.object(pipeline_classic, "datetime") as clock:
                        clock.now.return_value = datetime(
                            2026, 11, 27, tzinfo=timezone.utc
                        )
                        with patch.object(
                            pipeline_classic,
                            "listing_cars",
                            return_value=[{"cid": "123"}],
                        ):
                            with patch.object(
                                pipeline_classic, "fetch_detail"
                            ) as fetch:
                                with patch.object(
                                    pipeline_classic,
                                    "parse_ad",
                                    return_value={"ad_id": "123", "image_urls": []},
                                ):
                                    with patch.object(
                                        pipeline_classic, "classify", return_value="car"
                                    ):
                                        with patch.object(
                                            pipeline_classic,
                                            "collect_images",
                                            return_value=[],
                                        ):
                                            with patch.object(
                                                pipeline_classic, "export_ads"
                                            ):
                                                pipeline_classic.run(100, 0, 2)

            fetch.assert_not_called()
            self.assertEqual(current_partial.read_text(encoding="utf-8"), "")


class CollectImagesTests(unittest.TestCase):
    def test_hybrid_pipeline_saves_hybrid_score_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            output_dir = Path(folder) / "output"
            image_dir = output_dir / "2026-11-27" / "run_1" / "images"
            with patch.object(pipeline_hybrid, "OUT", output_dir):
                with patch.object(pipeline_hybrid, "download_image", return_value=True):
                    with patch.object(
                        pipeline_hybrid,
                        "score_image",
                        return_value={
                            "quality_score": 7.5,
                            "quality_metrics": {"model": "HyperIQA-KonIQ"},
                        },
                    ):
                        with patch.object(pipeline_hybrid.time, "sleep"):
                            result = pipeline_hybrid.collect_images(
                                object(),
                                {
                                    "ad_id": "123",
                                    "image_urls": ["https://example.test/a.jpg"],
                                },
                                0,
                                image_dir,
                            )

        self.assertEqual(result[0]["quality_score"], 7.5)
        self.assertEqual(
            result[0]["quality_metrics"]["model"], "HyperIQA-KonIQ"
        )
        self.assertEqual(result[0]["path"], "images/123_01.jpg")

    def test_classic_pipeline_saves_classic_score(self):
        with tempfile.TemporaryDirectory() as folder:
            output_dir = Path(folder) / "output"
            image_dir = output_dir / "2026-11-27" / "run_1" / "images"
            with patch.object(pipeline_classic, "OUT", output_dir):
                with patch.object(pipeline_classic, "download_image", return_value=True):
                    with patch.object(pipeline_classic, "score_image", return_value=7.5):
                        with patch.object(pipeline_classic.time, "sleep"):
                            result = pipeline_classic.collect_images(
                                object(),
                                {
                                    "ad_id": "123",
                                    "image_urls": ["https://example.test/a.jpg"],
                                },
                                0,
                                image_dir,
                            )

        self.assertEqual(result[0]["quality_score"], 7.5)
        self.assertNotIn("quality_metrics", result[0])
        self.assertEqual(result[0]["path"], "images/123_01.jpg")


if __name__ == "__main__":
    unittest.main()
