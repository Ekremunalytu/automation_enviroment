# Static Evaluation Corpus

This corpus contains twelve repository-authored, harmless source fixtures:
eight tuning samples and four holdout samples. Six represent declawed positive
or vulnerable code shapes and six are benign or coverage controls. Nothing in
this directory is executed; the evaluator only reads it inside the
network-disabled static analyzer container.

The manifest covers artifact role, network context, manifest and coverage,
dependency metadata, obfuscation, credential and download flows, webviews,
workspace trust, and dormancy/platform families. Each entry records a tree
SHA-256, provenance, safety state, split, and explicit rule/gate expectations.

Run the small tuning gate with:

```text
make static-eval SPLIT=tuning
```

Run the release baseline, including the untouched holdout, with:

```text
make static-eval SPLIT=all
```

Canonical JSON, derived Markdown, and the rule inventory are written below
`output/static-evaluation/`, which remains ignored. The initial expected
structural summary is 12 samples, 8 tuning, 4 holdout, and zero expectation
mismatches.
