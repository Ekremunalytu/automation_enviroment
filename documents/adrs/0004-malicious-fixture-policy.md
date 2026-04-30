# ADR 0004: Malicious Fixture Policy

- Status: Accepted (with 2026-04-30 addendum — see end of document)
- Date: 2026-04-17
- Related: ADR 0002 (Threat Model), ADR 0003 (Detection Taxonomy)

## Context

Detection rules cannot be validated using only benign fixtures. The current
corpus (`extensions/ms-python.python` and benign variants) can prove that
the analyzer produces stable activation reports; it cannot prove that the
analyzer detects anything.

At the same time, a malicious fixture corpus is a liability: accidental
installation on a developer workstation, leakage to a shared registry, or
uncontrolled execution of live samples in CI are all realistic failure
modes. This ADR defines how malicious fixtures are sourced, stored,
classified, and executed so that the corpus is useful without becoming the
operator's own supply chain incident.

## Decision

### 1. Corpus Location and Visibility

- Malicious fixtures live under `extensions/malicious/`.
- The directory is git-tracked so rule validation is reproducible.
- Top-level `README.md` inside `extensions/malicious/` carries a prominent
  warning and links to this ADR.
- The directory is **excluded** from any `code --install-extension` helper,
  Makefile target, or dev-setup script. A repository-wide guard test
  enforces this (section 6).

### 2. Isolation Tiers

Every fixture is assigned exactly one tier. Tier determines where and how
the fixture may run.

| Tier | Priority | Name | What it is | Where it runs |
|---|---|---|---|---|
| T1 | **PoC** | Synthetic canary | Code authored in-house to trigger a specific rule; no real malicious payload | Any environment, including CI, including local dev |
| T2 | Stretch | Declawed real sample | Real-world malicious sample with C2 endpoints rewritten to `127.0.0.1`, destructive operations replaced with markers, cryptographic keys neutralized | CI with network egress disabled; executor container without host network |
| T3 | Stretch (post-PoC) | Live sample | Real-world malicious sample, unmodified | Hardened local analyst environment **only**; NEVER CI; human operator acknowledgement required per run |

**PoC priority note (2026-04-17):** the 7-week PoC window is validated
against T1 canaries only. T2 and T3 remain fully in scope as defined
below — their tooling (`LABEL.yaml`, declawing notes, `make
test-security-live`) is part of the plan — but the PoC acceptance bar
does not require any T2 or T3 fixture to exist. Adding a T2 fixture
mid-PoC is welcome if time permits; T3 should not be attempted until
post-PoC.

T3 samples require a "break-glass" wrapper (`make test-security-live`) that
refuses to run if:

- `CI` env var is set
- Host network is reachable to the public internet without an egress proxy
- The operator has not passed `--i-understand-this-is-live` to the target

### 3. Fixture Manifest

Every fixture ships with a `LABEL.yaml` manifest next to the extension
directory:

```yaml
id: credstealer-001
tier: T2
source:
  kind: academic_dataset        # academic_dataset | virustotal | internal_canary | vendor_report
  reference: "vscode-malware-corpus-2024 / sample #47"
  sha256: "a1b2c3…"             # of the original VSIX archive
category:
  adversary_class: A1           # from ADR 0002
  taxonomy:
    - attack.T1555
    - attack.T1041
expected_detections:
  must_fire:
    - extrace.host.credential_read_then_network
  must_not_fire: []
declawing:
  notes:
    - "Original C2 host 'attacker.example.com' rewritten to 127.0.0.1"
    - "Exfiltration keys replaced with test-only tokens"
  verified_by: "operator@host 2026-04-17"
retention:
  expires: null                 # null = permanent; otherwise ISO-8601 date
```

- `expected_detections` is a **test contract**: the fixture-validation
  pipeline fails if `must_fire` rules do not fire or if `must_not_fire`
  rules do.
- `source.sha256` ties the fixture to an auditable origin; re-sourcing a
  fixture without updating this field is forbidden.
- `declawing` is required for T2 and must be `null` for T1 and T3.

### 4. Test Integration

Three execution surfaces, mutually exclusive by network/env posture:

- `make test-security` — security scaffold lane for T1/T2 policy checks;
  CI-targeted; no external network.
- `make test-security-live` — T3; local only; manual confirmation.
- benign baseline tests continue through the normal Python test lanes
  (`tests/platform/`, `tests/executor/`, `tests/smoke/`).

Current scaffold coverage checks (`tests/security/test_rule_coverage.py`)
assert:

- T1 canaries cover the PoC adversary classes A1/A2/A4/A6
- every T1 fixture declares at least one detection contract in `must_fire`
- no T3 fixtures are present in the current PoC scaffold

### 5. Sourcing Policy

- T1 canaries are authored in-house; no external sourcing concerns.
- T2 samples are sourced from:
  - academic datasets with documented provenance
  - VirusTotal private API (when available) with SHA-locked retrieval
  - vendor disclosure reports with a public write-up
  - internal honeypot captures
- T3 samples are sourced identically to T2 but are retained
  unmodified.
- Samples obtained through unofficial channels (forums, leak dumps,
  unattributed paste sites) are **not accepted** without a secondary
  source confirmation, because their provenance cannot be audited.

### 6. Repository Guardrails

Target guardrail set:

- `tests/security/test_fixture_hygiene.py`:
  - every subdirectory of `extensions/malicious/` has a `LABEL.yaml`
  - every `LABEL.yaml` satisfies the repo fixture contract
  - T3 fixtures are never referenced from files outside `extensions/malicious/`
    and `make test-security-live`
- Pre-commit hook (`scripts/check_fixture_install.py`):
  - fails the commit if any script or Makefile target installs an extension
    from a path under `extensions/malicious/`
- CI guard (`.github/workflows/ci.yml`):
  - `make test-security` runs with network policy denying external egress
  - CI job refuses to run `make test-security-live` (defense in depth; the
    Makefile target already refuses under `CI`)

Current implementation status (`2026-04-21`):

- present:
  - `tests/security/test_fixture_hygiene.py`
  - `tests/security/test_rule_coverage.py`
  - `make test-security`
  - `make test-security-live`
  - dedicated CI execution of `make test-security` with explicit egress policy
  - CI assertion that `make test-security-live` fails under `CI=true`
- not yet wired:
  - `scripts/check_fixture_install.py`

### 7. Output Handling for Malicious Runs

When analysis runs on a T2 or T3 fixture, output artifacts inherit the
fixture's tier for retention and distribution purposes:

- `output/activation_report_*.json` from T3 runs is not forwarded,
  uploaded, or indexed; it is written to a local-only path
  (`output/live/...`) and included in `.gitignore`.
- T2 output may be committed as baseline when rule validation needs a
  frozen example, but only after manual review confirms no stolen data
  ended up in the capture (the fixture is declawed, but declawing errors
  happen).

### 8. Operator Responsibilities

- Do not copy T3 fixtures off the analyst workstation.
- Do not run the harness extension or the executor container on a host
  that also carries production credentials.
- If a T3 run produces a report containing real secrets (because declawing
  failed or the sample exfiltrated something unexpected), treat the report
  as sensitive and rotate the affected credentials.

These responsibilities are operator-level, not platform-enforced.

## Consequences

### Positive

- Rule validation has a real signal: "fires on malicious, silent on benign"
  becomes a mechanical test.
- T1/T2/T3 separation lets CI stay aggressive without handling live
  malware.
- Fixture provenance is auditable.

### Negative

- Maintenance overhead: manifests, declawing notes, rule coverage matrix.
- T3 operation requires analyst discipline that cannot be fully automated.
- A fixture corpus is itself a regulated artifact in some jurisdictions;
  operators in regulated environments may need to exclude T2/T3 entirely.

### Follow-On

- Initial scaffold landed by `2026-04-20`:
  - `extensions/malicious/README.md`
  - T1 canary manifests for A1, A2, A4, and A6
  - `tests/security/test_fixture_hygiene.py`
  - `tests/security/test_rule_coverage.py`
  - `make test-security` and `make test-security-live`
- Remaining implementation gaps:
  - dedicated CI execution of `make test-security` with explicit egress policy
  - install-guard automation for `extensions/malicious/`
  - T2/T3 fixtures and runnable detection evaluation against them
- Revisit T3 handling once a hardened analyst environment specification
  exists; it is currently operator-defined.

## Addendum — 2026-04-30: Local-only operating model

This ADR was authored when the project ran a GitHub Actions `ci.yml`
pipeline whose `security-fixtures` job applied iptables egress rules
before invoking `make test-security`. That pipeline has been retired in
favor of a single-developer, local-appliance operating model
(`security.yml` for weekly Trivy/Bandit reports remains; `ci.yml` and
`docs-check.yml` were removed on 2026-04-30).

What changes:

- The "CI guard" enumerated in §6 ("CI job refuses to run
  `make test-security-live`") is no longer enforced at runner level.
  Defense in depth still holds because the Makefile target itself
  refuses under `CI=true` (`Makefile:240-243`) and refuses without
  `I_UNDERSTAND_THIS_IS_LIVE=1` (`Makefile:244-247`). The platform-level
  refusal moves from "two layers" to "one layer" (Makefile only).
- The "egress-disabled CI lane for T2" guarantee in §3 (T2 row) and
  §6 ("`make test-security` runs with network policy denying external
  egress") is no longer provided automatically. T2 fixtures, when
  introduced, must be executed inside the executor container's existing
  network isolation rather than relying on a runner-level iptables
  sandbox.

What does not change:

- T1 canary fixtures still safe to run anywhere, including local dev.
- T3 live samples still forbidden in any automated context; operator
  acknowledgement (`I_UNDERSTAND_THIS_IS_LIVE=1`) remains the single
  gate.
- `tests/security/test_fixture_hygiene.py` and
  `tests/security/test_rule_coverage.py` continue to enforce the
  corpus contract; they run via `make test-security` locally.

Trigger to revisit: if a second contributor joins, or if T2 fixtures
are added that genuinely need ambient egress isolation, the
`security-fixtures` job should be reintroduced — but only after
diagnosing the prior breakage (likely runner-image iptables drift).
