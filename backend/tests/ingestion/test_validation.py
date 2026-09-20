from io import BytesIO

import pymupdf
import pytest
from PIL import Image

from backend.app.ingestion.validation import UploadLimits, UploadProblem, validate_upload


def make_pdf(page_count: int = 1, encrypted: bool = False) -> bytes:
    document = pymupdf.open()
    for _ in range(page_count):
        document.new_page()
    if encrypted:
        output = document.tobytes(
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            owner_pw="owner",
            user_pw="user",
        )
    else:
        output = document.tobytes()
    document.close()
    return output


def make_png() -> bytes:
    image = Image.new("RGB", (20, 20), "white")
    stream = BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def test_accepts_pdf_by_signature_even_with_generic_declared_type():
    result = validate_upload(
        make_pdf(),
        "report.pdf",
        "application/octet-stream",
        UploadLimits(max_bytes=100_000, max_pages=2),
    )
    assert result.media_type == "application/pdf"
    assert result.page_count == 1


def test_rejects_content_that_does_not_match_filename():
    result = validate_upload(
        make_png(),
        "report.pdf",
        "application/pdf",
        UploadLimits(max_bytes=100_000, max_pages=2),
    )
    assert result.media_type == "image/png"


def test_rejects_payload_over_limit_before_parsing():
    with pytest.raises(UploadProblem, match="file_too_large"):
        validate_upload(
            b"x" * 101,
            "large.bin",
            "application/octet-stream",
            UploadLimits(max_bytes=100, max_pages=2),
        )


def test_rejects_encrypted_pdf():
    with pytest.raises(UploadProblem, match="encrypted_pdf"):
        validate_upload(
            make_pdf(encrypted=True),
            "locked.pdf",
            "application/pdf",
            UploadLimits(max_bytes=100_000, max_pages=2),
        )


def test_rejects_pdf_over_page_limit():
    with pytest.raises(UploadProblem, match="page_limit_exceeded"):
        validate_upload(
            make_pdf(page_count=3),
            "many.pdf",
            "application/pdf",
            UploadLimits(max_bytes=100_000, max_pages=2),
        )


def test_safe_name_cannot_escape_input_directory():
    result = validate_upload(
        make_pdf(),
        "../../my report.pdf",
        "application/pdf",
        UploadLimits(max_bytes=100_000, max_pages=2),
    )
    assert result.safe_name == "my_report.pdf"
