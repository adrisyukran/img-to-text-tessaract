from __future__ import annotations

from io import BytesIO

import pymupdf
from PIL import Image

from backend.app.domain.document import CanonicalDocument
from backend.app.ingestion.validation import ValidatedUpload
from backend.app.pipeline.render import RenderedPage


class SearchablePdfExporter:
    media_type = "application/pdf"
    extension = "pdf"

    def export(
        self,
        document: CanonicalDocument,
        source: ValidatedUpload,
        rendered_pages: list[RenderedPage],
    ) -> bytes:
        del rendered_pages
        if source.media_type == "application/pdf":
            output = pymupdf.open(  # type: ignore[no-untyped-call]
                stream=source.content,
                filetype="pdf",
            )
        else:
            output = pymupdf.open()  # type: ignore[no-untyped-call]
            with Image.open(BytesIO(source.content)) as image:
                width, height = image.size
            page = output.new_page(width=width * 72 / 96, height=height * 72 / 96)
            page.insert_image(page.rect, stream=source.content)  # type: ignore[no-untyped-call]

        for page_model in document.pages:
            if page_model.number > output.page_count:
                continue
            page = output[page_model.number - 1]
            for block in page_model.blocks:
                text = document.accepted_text_for_block(block.id)
                if not text:
                    continue
                rect = pymupdf.Rect(  # type: ignore[no-untyped-call]
                    block.bbox.x * page.rect.width,
                    block.bbox.y * page.rect.height,
                    (block.bbox.x + block.bbox.width) * page.rect.width,
                    (block.bbox.y + block.bbox.height) * page.rect.height,
                )
                font_size = max(4.0, min(36.0, rect.height * 0.8))
                while font_size >= 4.0:
                    inserted = page.insert_textbox(
                        rect,
                        text,
                        fontname="helv",
                        fontsize=font_size,
                        render_mode=3,
                        overlay=True,
                    )
                    if inserted >= 0:
                        break
                    font_size -= 0.5

        metadata = dict(output.metadata or {})
        metadata.update(
            {
                "keywords": "OCRPipelineVersion=1.0;TextLayerSource=accepted",
                "subject": f"Canonical OCR schema {document.schema_version}",
            }
        )
        output.set_metadata(metadata)
        stream = BytesIO()
        output.save(stream, garbage=4, deflate=True)  # type: ignore[no-untyped-call]
        output.close()  # type: ignore[no-untyped-call]
        return stream.getvalue()
