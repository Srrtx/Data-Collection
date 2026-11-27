import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import cv2
import numpy as np
import torch

from src.classic_score import score_image as classic_score_image
from quarantine.output.hybrid_score import _classical_metrics, rescore_export, score_image


with TemporaryDirectory() as directory:
    image_path = Path(directory) / "sample.jpg"
    checkerboard = (np.indices((32, 32)).sum(axis=0) % 2 * 255).astype(np.uint8)
    ok, encoded = cv2.imencode(
        ".jpg", np.repeat(checkerboard[:, :, None], 3, axis=2)
    )
    assert ok
    image_path.write_bytes(encoded.tobytes())
    image = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    hybrid_classical_score = _classical_metrics(image)["classical_score"]
    assert hybrid_classical_score == classic_score_image(image_path)

    with patch(
        "src.hybrid_score._load_hyperiqa",
        return_value=(lambda image: torch.tensor([0.75]), torch.device("cpu")),
    ):
        result = score_image(image_path)

    assert result["quality_score"] == 7.5
    assert result["quality_metrics"]["model"] == "HyperIQA-KonIQ"
    assert "laplacian_variance" in result["quality_metrics"]

    broken_path = Path(directory) / "broken.jpg"
    broken_path.write_bytes(b"not an image")
    broken = score_image(broken_path)
    assert broken["quality_score"] is None
    assert broken["quality_error"] == "image could not be decoded"

    export_path = Path(directory) / "ads.json"
    export_path.write_text(
        json.dumps({"ads": [{"images": [{"path": "sample.jpg"}]}]}),
        encoding="utf-8",
    )
    with patch(
        "src.hybrid_score._load_hyperiqa",
        return_value=(lambda image: torch.tensor([0.75]), torch.device("cpu")),
    ):
        assert rescore_export(export_path) == 1
    rescored = json.loads(export_path.read_text(encoding="utf-8"))
    assert rescored["ads"][0]["images"][0]["quality_score"] == 7.5
