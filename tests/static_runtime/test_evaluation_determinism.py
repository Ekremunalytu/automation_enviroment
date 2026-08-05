"""Normalized evaluation output is stable across identical inputs."""

from pathlib import Path

from static_runtime.evaluation import evaluate_corpus, render_markdown

CORPUS_ROOT = Path(__file__).resolve().parents[1] / "static_corpus"


def test_three_inhouse_evaluations_have_identical_normalized_results() -> None:
    results = [
        evaluate_corpus(
            manifest_path=CORPUS_ROOT / "manifest.json",
            corpus_root=CORPUS_ROOT / "samples",
            split="tuning",
            semgrep_enabled=False,
            evaluation_id=f"run-{index}",
        )
        for index in range(3)
    ]
    assert results[0].normalized_payload() == results[1].normalized_payload()
    assert results[1].normalized_payload() == results[2].normalized_payload()
    assert render_markdown(results[0]) == render_markdown(results[1])
