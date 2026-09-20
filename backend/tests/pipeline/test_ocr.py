from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from backend.app.pipeline.ocr import OCRProblem, TesseractEngine
from backend.app.pipeline.preprocess import PreprocessedPage, PreprocessMetadata
from backend.app.pipeline.render import RenderedPage


def make_page(tmp_path: Path) -> PreprocessedPage:
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"image")
    rendered = RenderedPage(1, image_path, 100, 200, 100, 200)
    metadata = PreprocessMetadata(
        rotation_degrees=0,
        deskew_degrees=0,
        contrast_applied=False,
        denoise_applied=False,
        threshold_method="none",
        operations=[],
    )
    return PreprocessedPage(rendered, image_path, metadata)


def test_tesseract_adapter_normalizes_words_and_omits_blank_tokens(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    result = {
        "block_num": [1, 1, 1],
        "par_num": [1, 1, 1],
        "line_num": [1, 1, 1],
        "word_num": [1, 2, 3],
        "left": [10, 30, 50],
        "top": [20, 20, 20],
        "width": [15, 15, 15],
        "height": [10, 10, 10],
        "conf": ["92", "48", "-1"],
        "text": ["Invoice", "lnvoice", " "],
    }

    def fake_image_to_data(*args, **kwargs):
        return result

    monkeypatch.setattr("pytesseract.image_to_data", fake_image_to_data)
    monkeypatch.setattr("pytesseract.image_to_string", lambda *args, **kwargs: "")
    monkeypatch.setattr(
        "PIL.Image.open",
        lambda *args, **kwargs: Image.fromarray(np.zeros((200, 100), dtype=np.uint8)),
    )

    spans = TesseractEngine().recognize(make_page(tmp_path))

    assert [span.id for span in spans] == ["p1-s0001", "p1-s0002"]
    assert [span.confidence for span in spans] == [0.92, 0.48]
    assert spans[0].bbox.x == 0.1
    assert spans[0].bbox.y == 0.1
    assert spans[0].source["block_num"] == 1


def test_missing_tesseract_binary_becomes_stable_problem(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "pytesseract.image_to_data",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("not installed")),
    )

    with pytest.raises(OCRProblem, match="ocr_unavailable"):
        TesseractEngine().recognize(make_page(tmp_path))
