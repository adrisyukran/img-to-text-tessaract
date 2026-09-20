import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePath
from typing import Literal

import pymupdf
from PIL import Image


@dataclass(frozen=True)
class UploadLimits:
    max_bytes: int
    max_pages: int


UploadMediaType = Literal["application/pdf", "image/png", "image/jpeg"]


@dataclass(frozen=True)
class ValidatedUpload:
    media_type: UploadMediaType
    safe_name: str
    page_count: int
    content: bytes


class UploadProblem(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def _safe_name(filename: str) -> str:
    basename = PurePath(filename.replace("\\", "/")).name
    stem, suffix = basename.rsplit(".", 1) if "." in basename else (basename, "")
    cleaned_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("._-") or "document"
    cleaned_suffix = re.sub(r"[^A-Za-z0-9]+", "", suffix).lower()
    return f"{cleaned_stem}.{cleaned_suffix}" if cleaned_suffix else cleaned_stem


def _classify(content: bytes) -> UploadMediaType | None:
    if content.startswith(b"%PDF-"):
        return "application/pdf"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return None


def validate_upload(
    content: bytes,
    filename: str,
    declared_type: str,
    limits: UploadLimits,
) -> ValidatedUpload:
    del declared_type
    if len(content) > limits.max_bytes:
        raise UploadProblem("file_too_large", "The file exceeds the upload size limit.")
    media_type = _classify(content)
    if media_type is None:
        raise UploadProblem("unsupported_file", "Only PDF, PNG, and JPEG files are supported.")

    if media_type == "application/pdf":
        try:
            document = pymupdf.open(stream=content, filetype="pdf")  # type: ignore[no-untyped-call]
        except Exception as exc:
            raise UploadProblem("invalid_pdf", "The PDF could not be opened.") from exc
        try:
            if document.needs_pass:
                raise UploadProblem("encrypted_pdf", "Password-protected PDFs are not supported.")
            page_count = document.page_count
        finally:
            document.close()  # type: ignore[no-untyped-call]
        if page_count > limits.max_pages:
            raise UploadProblem("page_limit_exceeded", "The PDF has too many pages.")
    else:
        try:
            with Image.open(BytesIO(content)) as image:
                image.verify()
        except Exception as exc:
            raise UploadProblem("invalid_image", "The image could not be decoded.") from exc
        page_count = 1

    suffix = (
        ".pdf"
        if media_type == "application/pdf"
        else ".png"
        if media_type == "image/png"
        else ".jpg"
    )
    safe_name = _safe_name(filename)
    if not safe_name.lower().endswith(suffix):
        safe_name = f"{PurePath(safe_name).stem}{suffix}"
    return ValidatedUpload(media_type, safe_name, page_count, content)
