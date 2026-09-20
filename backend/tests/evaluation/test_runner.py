import json
from pathlib import Path

from evaluation.run import evaluate_corpus


def test_evaluation_runner_writes_versioned_results(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    ground_truth = tmp_path / "truth.txt"
    ground_truth.write_text("A clean invoice", encoding="utf-8")
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "samples": [
                    {
                        "id": "sample-1",
                        "title": "Sample",
                        "pdf": "sample.pdf",
                        "ground_truth": "truth.txt",
                        "page_count": 1,
                        "labels": ["clean"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "results.json"

    evaluate_corpus(
        manifest,
        output,
        hypotheses={"sample-1": "A clean invoice"},
        elapsed_ms={"sample-1": 123.4},
    )

    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["schema_version"] == "1.0"
    assert result["samples"][0]["raw"]["wer"] == 0
    assert result["samples"][0]["elapsed_ms"] == 123.4
