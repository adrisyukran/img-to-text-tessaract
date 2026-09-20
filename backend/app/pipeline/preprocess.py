from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
from pydantic import BaseModel, ConfigDict

from backend.app.pipeline.render import RenderedPage


class PreprocessMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rotation_degrees: int
    deskew_degrees: float
    contrast_applied: bool
    denoise_applied: bool
    threshold_method: Literal["none", "otsu", "adaptive"]
    operations: list[str]


@dataclass(frozen=True)
class PreprocessedPage:
    rendered: RenderedPage
    image_path: Path
    metadata: PreprocessMetadata


def needs_contrast(image: np.ndarray) -> bool:
    return float(np.std(image)) < 45


def estimate_skew(image: np.ndarray) -> float:
    coordinates = np.column_stack(np.where(image < 200))
    if len(coordinates) < 20:
        return 0.0
    rectangle = cv2.minAreaRect(coordinates.astype(np.float32))
    angle = float(rectangle[-1])
    if angle < -45:
        angle = 90 + angle
    if angle > 45:
        angle -= 90
    return angle


def choose_threshold(image: np.ndarray) -> Literal["none", "otsu", "adaptive"]:
    if float(np.std(image)) < 18:
        return "adaptive"
    histogram = cv2.calcHist([image], [0], None, [32], [0, 256]).ravel()
    occupied_bins = int(np.count_nonzero(histogram > 0))
    return "otsu" if occupied_bins <= 10 else "none"


def _rotate(image: np.ndarray, degrees: float) -> np.ndarray:
    if abs(degrees) < 0.5:
        return image
    height, width = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), degrees, 1)
    return cv2.warpAffine(
        image,
        matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )


def preprocess_page(page: RenderedPage, output_dir: Path) -> PreprocessedPage:
    image = cv2.imread(str(page.image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError("unreadable_page_image")
    operations: list[str] = ["grayscale"]
    contrast_applied = needs_contrast(image)
    if contrast_applied:
        image = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(image)
        operations.append("contrast")

    skew = estimate_skew(image)
    deskew = -max(-12.0, min(12.0, skew))
    if abs(deskew) >= 0.5:
        image = _rotate(image, deskew)
        operations.append("deskew")

    denoise_applied = float(cv2.Laplacian(image, cv2.CV_64F).var()) < 180
    if denoise_applied:
        image = cv2.medianBlur(image, 3)
        operations.append("denoise")

    threshold_method = choose_threshold(image)
    if threshold_method == "otsu":
        _, image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        operations.append("otsu")
    elif threshold_method == "adaptive":
        image = cv2.adaptiveThreshold(
            image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11,
        )
        operations.append("adaptive")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"page-{page.page_number:04d}-processed.png"
    if not cv2.imwrite(str(output_path), image):
        raise ValueError("preprocessed_page_write_failed")
    metadata = PreprocessMetadata(
        rotation_degrees=0,
        deskew_degrees=deskew,
        contrast_applied=contrast_applied,
        denoise_applied=denoise_applied,
        threshold_method=threshold_method,
        operations=operations,
    )
    return PreprocessedPage(page, output_path, metadata)
