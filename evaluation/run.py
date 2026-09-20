import argparse
import hashlib
import json
import shutil
import tempfile
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from backend.app.ingestion.validation import UploadLimits, validate_upload
from backend.app.pipeline.ocr import TesseractEngine
from backend.app.pipeline.preprocess import preprocess_page
from backend.app.pipeline.render import render_pages
from backend.app.storage.workspaces import JobWorkspace
from evaluation.metrics import TextMetrics, score_text


def evaluate_corpus(
    manifest_path: Path,
    output_path: Path,
    hypotheses: Mapping[str, str],
    elapsed_ms: Mapping[str, float] | None = None,
    corrected_hypotheses: Mapping[str, str] | None = None,
    correction_counts: Mapping[str, int] | None = None,
    provider_metrics: Mapping[str, Mapping[str, int | float | str]] | None = None,
) -> dict[str, object]:
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    elapsed = elapsed_ms or {}
    samples: list[dict[str, object]] = []
    metrics_by_sample: list[TextMetrics] = []
    corrected_metrics: list[TextMetrics] = []
    corrected = corrected_hypotheses or {}
    counts = correction_counts or {}
    provider = provider_metrics or {}
    for entry in manifest["samples"]:
        sample_id = entry["id"]
        truth_path = manifest_path.parent / entry["ground_truth"]
        reference = truth_path.read_text(encoding="utf-8")
        metrics = score_text(reference, hypotheses[sample_id])
        metrics_by_sample.append(metrics)
        sample_result: dict[str, object] = {
            "id": sample_id,
            "title": entry["title"],
            "labels": entry.get("labels", []),
            "page_count": entry["page_count"],
            "elapsed_ms": float(elapsed.get(sample_id, 0)),
            "raw": metrics.as_dict(),
            "correction_count": int(counts.get(sample_id, 0)),
        }
        if sample_id in corrected:
            corrected_score = score_text(reference, corrected[sample_id])
            corrected_metrics.append(corrected_score)
            sample_result["corrected"] = corrected_score.as_dict()
        if sample_id in provider:
            sample_result["provider"] = dict(provider[sample_id])
        samples.append(sample_result)
    aggregate = {
        "cer": sum(item.cer for item in metrics_by_sample) / len(metrics_by_sample),
        "wer": sum(item.wer for item in metrics_by_sample) / len(metrics_by_sample),
    }
    if corrected_metrics:
        aggregate["corrected_cer"] = (
            sum(item.cer for item in corrected_metrics) / len(corrected_metrics)
        )
        aggregate["corrected_wer"] = (
            sum(item.wer for item in corrected_metrics) / len(corrected_metrics)
        )
    result: dict[str, object] = {
        "schema_version": "1.0",
        "generated_from_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "samples": samples,
        "aggregate": aggregate,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _tesseract_hypotheses(manifest_path: Path) -> tuple[dict[str, str], dict[str, float]]:
    manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    temporary_root = Path(tempfile.mkdtemp(prefix="scanned-pdf-evaluation-"))
    engine = TesseractEngine()
    hypotheses: dict[str, str] = {}
    elapsed_ms: dict[str, float] = {}
    try:
        for entry in manifest["samples"]:
            sample_id = str(entry["id"])
            source = (manifest_path.parent / str(entry["pdf"])).resolve()
            started = time.perf_counter()
            upload = validate_upload(
                source.read_bytes(),
                source.name,
                "application/pdf",
                UploadLimits(15_000_000, 12),
            )
            workspace = JobWorkspace.create(temporary_root, "eval-" + sample_id)
            try:
                rendered = render_pages(upload, workspace, dpi=150)
                text_parts: list[str] = []
                for page in rendered:
                    processed = preprocess_page(page, workspace.pages_dir)
                    text_parts.extend(span.text for span in engine.recognize(processed))
                hypotheses[sample_id] = " ".join(text_parts)
            finally:
                workspace.delete()
            elapsed_ms[sample_id] = (time.perf_counter() - started) * 1000
    finally:
        shutil.rmtree(temporary_root, ignore_errors=True)
    return hypotheses, elapsed_ms


def _public_result(
    result: dict[str, object],
    *,
    engine: str,
    preprocessing_profile: str,
    correction_provider: str,
    run_environment: str,
) -> dict[str, object]:
    aggregate_value = cast(dict[str, Any], result["aggregate"])
    aggregate: dict[str, object] = {
        "raw": {
            "cer": float(aggregate_value["cer"]),
            "wer": float(aggregate_value["wer"]),
        },
        "corrected": None,
    }
    if "corrected_cer" in aggregate_value and "corrected_wer" in aggregate_value:
        aggregate["corrected"] = {
            "cer": float(aggregate_value["corrected_cer"]),
            "wer": float(aggregate_value["corrected_wer"]),
        }
    public_samples: list[dict[str, object]] = []
    for sample_value in cast(list[dict[str, Any]], result["samples"]):
        raw = cast(dict[str, Any], sample_value["raw"])
        corrected_value = sample_value.get("corrected")
        corrected = None
        if corrected_value is not None:
            corrected_metrics = cast(dict[str, Any], corrected_value)
            corrected = {
                "cer": float(corrected_metrics["cer"]),
                "wer": float(corrected_metrics["wer"]),
            }
        public_samples.append(
            {
                "id": str(sample_value["id"]),
                "title": str(sample_value["title"]),
                "labels": list(sample_value.get("labels", [])),
                "page_count": int(sample_value["page_count"]),
                "elapsed_ms": float(sample_value["elapsed_ms"]),
                "raw": {"cer": float(raw["cer"]), "wer": float(raw["wer"])},
                "corrected": corrected,
                "correction_count": int(sample_value["correction_count"]),
                "representative_diffs": [],
            }
        )
    return {
        "schema_version": "1.0",
        "measured": True,
        "generated_from_manifest_sha256": result["generated_from_manifest_sha256"],
        "engine": engine,
        "preprocessing_profile": preprocessing_profile,
        "correction_provider": correction_provider,
        "run_environment": run_environment,
        "aggregate": aggregate,
        "samples": public_samples,
        "methodology": [
            "CER and WER use whitespace-normalized synthetic ground truth.",
            "Raw OCR is compared before any provider correction.",
        ],
        "limitations": [
            "Three synthetic printed English pages are not a general accuracy guarantee.",
            "This run does not measure handwriting, multilingual text, or complex tables.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Score OCR hypotheses against the bundled corpus.")
    parser.add_argument("--manifest", type=Path, default=Path("evaluation/corpus/manifest.json"))
    parser.add_argument("--output", type=Path, default=Path("evaluation/results.json"))
    parser.add_argument("--public-output", type=Path)
    parser.add_argument("--engine", choices=["hypotheses", "tesseract"], default="hypotheses")
    parser.add_argument("--run-environment", default="local")
    parser.add_argument(
        "--hypotheses-json",
        type=Path,
        help="JSON object mapping sample IDs to raw OCR text.",
    )
    args = parser.parse_args()
    if args.engine == "tesseract":
        hypotheses, elapsed_ms = _tesseract_hypotheses(args.manifest)
    elif args.hypotheses_json is None:
        parser.error("--hypotheses-json is required to run evaluation")
    else:
        hypotheses = json.loads(args.hypotheses_json.read_text(encoding="utf-8"))
        elapsed_ms = {}
    result = evaluate_corpus(
        args.manifest,
        args.output,
        hypotheses=hypotheses,
        elapsed_ms=elapsed_ms,
    )
    if args.public_output is not None:
        public = _public_result(
            result,
            engine="Tesseract" if args.engine == "tesseract" else "Provided hypotheses",
            preprocessing_profile="grayscale + contrast + bounded deskew + threshold",
            correction_provider="none (raw OCR baseline)",
            run_environment=args.run_environment,
        )
        args.public_output.parent.mkdir(parents=True, exist_ok=True)
        args.public_output.write_text(
            json.dumps(public, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
