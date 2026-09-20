from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SampleProblem(ValueError):
    pass


class PublicSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    page_count: int = Field(ge=1)
    preview_url: str
    labels: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class SampleAsset:
    public: PublicSample
    pdf_path: Path
    ground_truth_path: Path


class SampleRegistry:
    def __init__(self, assets: list[SampleAsset]) -> None:
        self._assets = {asset.public.id: asset for asset in assets}
        self._ordered_ids = [asset.public.id for asset in assets]

    @classmethod
    def default(cls) -> SampleRegistry:
        manifest = Path(__file__).resolve().parents[3] / "evaluation" / "corpus" / "manifest.json"
        return cls.from_manifest(manifest)

    @classmethod
    def from_manifest(cls, manifest_path: Path) -> SampleRegistry:
        try:
            payload: Any = json.loads(manifest_path.read_text(encoding="utf-8"))
            entries = payload["samples"]
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise SampleProblem("invalid sample manifest") from exc
        if not isinstance(entries, list):
            raise SampleProblem("invalid sample manifest")

        corpus_root = manifest_path.parent.resolve()
        evaluation_root = corpus_root.parent
        assets: list[SampleAsset] = []
        seen: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise SampleProblem("invalid sample entry")
            try:
                sample_id = str(entry["id"])
                if sample_id in seen:
                    raise SampleProblem(f"duplicate sample id: {sample_id}")
                seen.add(sample_id)
                pdf_path = (corpus_root / str(entry["pdf"])).resolve()
                ground_truth_path = (corpus_root / str(entry["ground_truth"])).resolve()
                if not pdf_path.is_relative_to(corpus_root):
                    raise SampleProblem("sample PDF path escapes corpus")
                if not ground_truth_path.is_relative_to(evaluation_root):
                    raise SampleProblem("sample ground truth path escapes evaluation")
                if pdf_path.suffix.lower() != ".pdf" or not pdf_path.is_file():
                    raise SampleProblem("sample has unsupported or missing PDF media")
                if not ground_truth_path.is_file():
                    raise SampleProblem("sample ground truth is missing")
                public = PublicSample(
                    id=sample_id,
                    title=str(entry["title"]),
                    description=str(entry["description"]),
                    page_count=int(entry["page_count"]),
                    preview_url=f"/api/v1/samples/{sample_id}/preview",
                    labels=[str(label) for label in entry.get("labels", [])],
                )
            except (KeyError, TypeError, ValueError) as exc:
                if isinstance(exc, SampleProblem):
                    raise
                raise SampleProblem("invalid sample entry") from exc
            assets.append(SampleAsset(public, pdf_path, ground_truth_path))
        return cls(assets)

    def public_samples(self) -> list[PublicSample]:
        return [self._assets[sample_id].public for sample_id in self._ordered_ids]

    def get(self, sample_id: str) -> SampleAsset | None:
        return self._assets.get(sample_id)
