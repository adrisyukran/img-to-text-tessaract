from pathlib import Path
from typing import Protocol

import pytesseract  # type: ignore[import-untyped]
from PIL import Image

from backend.app.domain.document import BoundingBox, OCRSpan
from backend.app.pipeline.preprocess import PreprocessedPage


class OCRProblem(RuntimeError):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


class OCREngine(Protocol):
    def recognize(self, page: PreprocessedPage) -> list[OCRSpan]:
        raise NotImplementedError


class TesseractEngine:
    def __init__(self, language: str = "eng", timeout_seconds: float = 30) -> None:
        self.language = language
        self.timeout_seconds = timeout_seconds

    def recognize(self, page: PreprocessedPage) -> list[OCRSpan]:
        image_path: Path = page.image_path
        try:
            image = Image.open(image_path)
            width, height = image.size
            data = pytesseract.image_to_data(
                image,
                lang=self.language,
                config="--oem 1 --psm 3",
                output_type=pytesseract.Output.DICT,
                timeout=self.timeout_seconds,
            )
        except RuntimeError as exc:
            code = "ocr_timeout" if "timeout" in str(exc).lower() else "ocr_unavailable"
            raise OCRProblem(code, "Tesseract could not process this page.") from exc
        except (OSError, pytesseract.TesseractNotFoundError) as exc:
            raise OCRProblem(
                "ocr_unavailable",
                "Tesseract is not installed or unavailable.",
            ) from exc
        finally:
            if "image" in locals():
                image.close()

        spans: list[OCRSpan] = []
        for index, raw_text in enumerate(data.get("text", [])):
            text = str(raw_text).strip()
            try:
                confidence = float(data["conf"][index])
            except (KeyError, IndexError, TypeError, ValueError):
                continue
            if not text or confidence < 0:
                continue
            left = int(data["left"][index])
            top = int(data["top"][index])
            box_width = int(data["width"][index])
            box_height = int(data["height"][index])
            spans.append(
                OCRSpan(
                    id=f"p{page.rendered.page_number}-s{len(spans) + 1:04d}",
                    text=text,
                    bbox=BoundingBox(
                        x=max(0, left) / width,
                        y=max(0, top) / height,
                        width=max(0, box_width) / width,
                        height=max(0, box_height) / height,
                    ),
                    confidence=max(0.0, min(1.0, confidence / 100)),
                    source={
                        "block_num": int(data["block_num"][index]),
                        "par_num": int(data["par_num"][index]),
                        "line_num": int(data["line_num"][index]),
                        "word_num": int(data["word_num"][index]),
                    },
                )
            )
        return spans
