import json
from pathlib import Path

import pytest

from backend.app.ingestion.samples import SampleProblem, SampleRegistry


def write_manifest(root: Path, samples: list[dict[str, object]]) -> Path:
    evaluation = root / "evaluation"
    corpus = evaluation / "corpus"
    ground_truth = evaluation / "ground_truth"
    corpus.mkdir(parents=True)
    ground_truth.mkdir()
    (corpus / "sample.pdf").write_bytes(b"%PDF-test")
    (ground_truth / "sample.txt").write_text("truth", encoding="utf-8")
    manifest = corpus / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": "1.0", "samples": samples}), encoding="utf-8")
    return manifest


def sample_entry(sample_id: str = "sample") -> dict[str, object]:
    return {
        "id": sample_id,
        "title": "Sample",
        "description": "A sample document.",
        "labels": ["printed"],
        "page_count": 1,
        "pdf": "sample.pdf",
        "ground_truth": "../ground_truth/sample.txt",
    }


def test_default_registry_returns_public_samples_without_paths() -> None:
    registry = SampleRegistry.default()

    assert [sample.id for sample in registry.public_samples()] == [
        "clean-letter",
        "skewed-report",
        "noisy-invoice",
    ]
    public = registry.public_samples()[0].model_dump()
    assert "pdf_path" not in public
    assert "ground_truth" not in public


def test_registry_rejects_duplicate_ids_and_escaping_assets(tmp_path: Path) -> None:
    entry = sample_entry()
    manifest = write_manifest(tmp_path, [entry, entry.copy()])
    with pytest.raises(SampleProblem, match="duplicate"):
        SampleRegistry.from_manifest(manifest)

    escaping = sample_entry()
    escaping["pdf"] = "../../outside.pdf"
    manifest = write_manifest(tmp_path / "escape", [escaping])
    with pytest.raises(SampleProblem, match="path"):
        SampleRegistry.from_manifest(manifest)


def test_registry_requires_ground_truth_and_supported_pdf(tmp_path: Path) -> None:
    entry = sample_entry()
    entry["ground_truth"] = "../ground_truth/missing.txt"
    manifest = write_manifest(tmp_path / "missing", [entry])
    with pytest.raises(SampleProblem, match="ground truth"):
        SampleRegistry.from_manifest(manifest)

    entry = sample_entry()
    entry["pdf"] = "sample.txt"
    manifest = write_manifest(tmp_path / "type", [entry])
    (manifest.parent / "sample.txt").write_text("not a pdf", encoding="utf-8")
    with pytest.raises(SampleProblem, match="media"):
        SampleRegistry.from_manifest(manifest)
