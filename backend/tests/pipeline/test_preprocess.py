from pathlib import Path

import cv2
import numpy as np

from backend.app.pipeline.preprocess import (
    choose_threshold,
    estimate_skew,
    needs_contrast,
    preprocess_page,
)
from backend.app.pipeline.render import RenderedPage


def rotated_fixture(path: Path) -> RenderedPage:
    image = np.full((300, 500), 255, dtype=np.uint8)
    for y in (80, 130, 180):
        cv2.rectangle(image, (90, y), (410, y + 10), 20, -1)
    matrix = cv2.getRotationMatrix2D((250, 150), 4, 1)
    rotated = cv2.warpAffine(image, matrix, (500, 300), borderValue=255)
    cv2.imwrite(str(path), rotated)
    return RenderedPage(1, path, 500, 300, 500, 300)


def test_skew_estimate_detects_small_rotation(tmp_path: Path):
    page = rotated_fixture(tmp_path / "rotated.png")
    assert 3 <= abs(estimate_skew(cv2.imread(str(page.image_path), cv2.IMREAD_GRAYSCALE))) <= 5


def test_low_contrast_page_needs_contrast():
    image = np.full((10, 10), 128, dtype=np.uint8)
    image[2:8, 2:8] = 145
    assert needs_contrast(image)


def test_threshold_strategy_is_conservative_for_crisp_page():
    image = np.zeros((100, 100), dtype=np.uint8)
    image[20:80, 20:80] = 255
    assert choose_threshold(image) in {"none", "otsu"}


def test_preprocess_writes_new_image_and_records_operations(tmp_path: Path):
    page = rotated_fixture(tmp_path / "original.png")

    result = preprocess_page(page, tmp_path / "processed")

    assert result.image_path.exists()
    assert result.image_path.name == "page-0001-processed.png"
    assert result.metadata.operations
    assert page.image_path.read_bytes() == (tmp_path / "original.png").read_bytes()
