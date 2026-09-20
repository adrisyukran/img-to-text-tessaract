import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.utils import ImageReader  # type: ignore[import-untyped]
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]

ROOT = Path(__file__).parent
CORPUS = ROOT / "corpus"
GROUND_TRUTH = ROOT / "ground_truth"
SEED = 20260920

@dataclass(frozen=True)
class CorpusSample:
    id: str
    title: str
    description: str
    filename: str
    truth: str
    labels: list[str]
    text: str


SAMPLES = [
    CorpusSample(
        id="clean-letter",
        title="Clean letter",
        description="A high-contrast printed page with generous spacing.",
        filename="clean-letter.pdf",
        truth="clean-letter.txt",
        labels=["clean", "printed"],
        text=(
            "Field Notes 1987\n\n"
            "A readable archive begins with a faithful record. "
            "This short letter is intentionally clear so the baseline can separate "
            "OCR quality from document complexity."
        ),
    ),
    CorpusSample(
        id="skewed-report",
        title="Skewed report",
        description="A lightly rotated page that benefits from deskewing.",
        filename="skewed-report.pdf",
        truth="skewed-report.txt",
        labels=["skew", "printed"],
        text=(
            "Quarterly Archive Report\n\n"
            "The restoration team reviewed 42 folders during the spring survey. "
            "Three folders require a second pass before publication."
        ),
    ),
    CorpusSample(
        id="noisy-invoice",
        title="Noisy invoice",
        description="A low-contrast page with deterministic scan noise.",
        filename="noisy-invoice.pdf",
        truth="noisy-invoice.txt",
        labels=["noise", "invoice"],
        text=(
            "Invoice 2048\n\n"
            "Archive supplies                         120.00\n"
            "Scanning service                          85.00\n"
            "Total                                    205.00"
        ),
    ),
]


def _font(size: int) -> Any:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _page_image(text: str, label: str) -> Image.Image:
    image = Image.new("L", (1275, 1650), color=255)
    draw = ImageDraw.Draw(image)
    draw.text((145, 125), label, fill=35, font=_font(32))
    y = 260
    for line in text.splitlines():
        draw.text((145, y), line, fill=35, font=_font(29))
        y += 70
    return image


def _transform(image: Image.Image, sample_id: str) -> Image.Image:
    if sample_id == "skewed-report":
        return image.rotate(3.5, expand=False, fillcolor=255, resample=Image.Resampling.BICUBIC)
    if sample_id == "noisy-invoice":
        array = np.asarray(image, dtype=np.int16)
        rng = np.random.default_rng(SEED)
        noise = rng.normal(0, 10, array.shape)
        noisy = np.clip(array + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy).filter(ImageFilter.GaussianBlur(radius=0.35))
    return image


def _write_pdf(image: Image.Image, destination: Path) -> None:
    png_path = destination.with_suffix(".png")
    image.save(png_path, format="PNG")
    pdf = canvas.Canvas(str(destination), pagesize=(612, 792))
    pdf.drawImage(ImageReader(str(png_path)), 0, 0, width=612, height=792, mask="auto")
    pdf.showPage()
    pdf.save()
    png_path.unlink()


def generate(replace: bool = False) -> Path:
    CORPUS.mkdir(parents=True, exist_ok=True)
    GROUND_TRUTH.mkdir(parents=True, exist_ok=True)
    manifest_path = CORPUS / "manifest.json"
    outputs = [manifest_path]
    for sample in SAMPLES:
        outputs.extend([CORPUS / sample.filename, GROUND_TRUTH / sample.truth])
    if not replace and any(path.exists() for path in outputs):
        raise FileExistsError("corpus exists; use --replace to regenerate it")

    for sample in SAMPLES:
        text = sample.text
        (GROUND_TRUTH / sample.truth).write_text(text + "\n", encoding="utf-8")
        image = _transform(_page_image(text, sample.title.upper()), sample.id)
        _write_pdf(image, CORPUS / sample.filename)

    manifest = {
        "schema_version": "1.0",
        "seed": SEED,
        "samples": [
            {
                "id": sample.id,
                "title": sample.title,
                "description": sample.description,
                "pdf": sample.filename,
                "ground_truth": f"../ground_truth/{sample.truth}",
                "page_count": 1,
                "labels": sample.labels,
            }
            for sample in SAMPLES
        ],
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    print(generate(replace=args.replace))
