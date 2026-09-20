import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

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
