# ADR 0003: Detection Taxonomy and Finding Contract

- Status: Accepted
- Date: 2026-04-17
- Related: ADR 0002 (Threat Model), ADR 0004 (Malicious Fixture Policy)

## Context

Writing detection rules without a taxonomy produces a rule archive that
cannot be audited, deduplicated, or retired. ADR 0002 defines what we are
looking for; this ADR defines how findings are structured, named, scored,
and surfaced.

The existing `ActivationReport` contract (Week 2) is a **quality and
verification** contract — it describes how well the analyzer observed the
extension. It is not a detection contract. This ADR introduces a sibling
contract, `DetectionReport`, carried alongside `ActivationReport` but owned
separately.

## Decision

### 1. Taxonomy Alignment

Detection categories align with the MITRE ATT&CK Enterprise matrix where
possible, plus a local extension-specific namespace for categories ATT&CK
does not cover cleanly.

| Namespace | Purpose | Example |
|---|---|---|
| `attack.T####` | Direct MITRE technique mapping | `attack.T1555` (credential access from password stores) |
| `extrace.ext.*` | Extension-specific categories without a clean ATT&CK equivalent | `extrace.ext.typosquat_naming`, `extrace.ext.activation_gated_payload` |
| `extrace.host.*` | Host-facing runtime behavior | `extrace.host.child_process_spawn`, `extrace.host.dns_exfiltration` |

A finding MUST carry at least one category. Multiple categories are allowed
when behavior spans domains (e.g. credential read + network exfiltration).

### 2. Severity Scale

Severity is a fixed ordinal, not a free-form tag:

| Level | Meaning | Example |
|---|---|---|
| `critical` | Behavior that is malicious under any reasonable interpretation | SSH key read immediately followed by POST to attacker-controlled host |
| `high` | Behavior that is overwhelmingly associated with malicious intent | Remote-loader pattern (`eval(fetch(...))`); cryptominer signature |
| `medium` | Suspicious behavior that requires corroboration | Broad file read of `~/.aws/*` without obvious benign justification |
| `low` | Minor anomaly, informational weight only | Unusual activation event combination for the extension category |
| `info` | Observational, no implied verdict | Extension is a typosquat candidate (name proximity) |

Severity is a property of the **detection rule**, not the extension. An
extension's overall verdict is a rollup of its findings (section 5).

### 3. Confidence

Orthogonal to severity. Expresses the detector's certainty that its
observation is correct (not whether the underlying behavior is malicious).

| Level | Meaning |
|---|---|
| `high` | Direct capture of the behavior (e.g. literal exfiltration POST body visible) |
| `medium` | Strong indirect evidence (e.g. DNS resolution + outbound TLS + known bad reputation) |
| `low` | Heuristic match; requires analyst review |

### 4. Finding Contract

A detection finding is serialized as:

```json
{
  "id": "01JK8V3YPR5ZDP4ZC8Q1MTN7BF",
  "rule_id": "extrace.host.credential_read_then_network",
  "rule_version": "1.0.0",
  "categories": ["attack.T1555", "attack.T1041"],
  "severity": "critical",
  "confidence": "high",
  "title": "Credential file read followed by outbound network request",
  "description": "Extension read ~/.ssh/id_rsa during activation, then issued an HTTPS POST to a host not referenced in its manifest.",
  "evidence": [
    {"type": "filesystem_read", "event_id": "fs-00012", "path": "~/.ssh/id_rsa"},
    {"type": "network_request", "event_id": "net-00045", "host": "c2.example.invalid", "method": "POST"}
  ],
  "adversary_class": "A1",
  "mitigation_hint": null
}
```

- `id` is a ULID generated per finding per run.
- `rule_id` follows the taxonomy namespacing from section 1.
- `rule_version` enables rule evolution without breaking historic findings.
- `evidence[].event_id` references events inside the corresponding
  `ActivationReport` so the UI can deep-link from finding to raw capture.
- `adversary_class` references ADR 0002 classes A1-A7 when applicable.

### 5. Verdict Rollup

The extension-level verdict is derived deterministically from the finding
list. This avoids hidden heuristics and lets operators audit verdicts.

| Condition | Verdict |
|---|---|
| ≥1 finding at `critical` severity with `high` confidence | `malicious` |
| ≥2 findings at `high` severity (any confidence ≥ `medium`) | `malicious` |
| 1 finding at `high` or ≥3 at `medium` | `suspicious` |
| Only `low` / `info` findings | `clean_with_notes` |
| No findings | `clean` |
| Analysis incomplete (executor failure, verification gap unresolved, timeout) | `inconclusive` |

`inconclusive` **dominates** all other verdicts: if analysis could not
observe the relevant surface, we do not claim cleanliness. This is the
explicit linkage to the `automation_health` and `verification_gap` fields
already in `ActivationReport`.

### 6. DetectionReport Contract Location

- Authoritative schema lives under `packages/analysis_contracts/detection/`.
- Owned by the backend, validated with Pydantic v2, consumed by UI via
  generated TypeScript types (see Week 4D UI refactor plan in
  `REFACTOR_OPTIMIZATION.md` §2.6).
- The existing `ActivationReport` is **not** modified to embed findings;
  the two reports travel together (`report_bundle`) so quality and
  detection concerns stay decoupled.

### 7. Rule Lifecycle

Rules progress through explicit states. No rule ships to production without
passing each gate.

1. **Draft** — rule authored; target fixtures declared.
2. **Fixture-validated** — detects all positive fixtures, detects zero
   negative fixtures. Fixtures governed by ADR 0004.
3. **Smoke-validated** — runs in `make test-security` against the full
   malicious+benign corpus without regressing other rules.
4. **Production** — eligible to contribute to verdict rollup.
5. **Deprecated** — superseded by a newer rule; kept for historical finding
   interpretation via `rule_version`.

**PoC lifecycle mode (2026-04-17):** during the 7-week PoC window, gates
2 and 3 may be combined when the corpus is small enough (≤ 10 fixtures
total). A rule can move Draft → Production in a single pass if it
satisfies both gates against the available corpus. This shortcut is
**PoC-scope only**; the four-gate lifecycle becomes mandatory again
once the corpus exceeds the PoC bar (ADR 0004 §4) or the project moves
past PoC acceptance.

A rule in `Draft` or `Fixture-validated` MAY emit findings with
`confidence: low` and severity capped at `medium`; its findings never
escalate a verdict past `suspicious`.

### 8. Banned Patterns in Rule Authoring

- No rule may depend on the presence of `output/` filesystem state from
  a previous run.
- No rule may mutate the `ActivationReport` or any shared object.
- No rule may import from `workflows/`, `executor/`, or `ui/` — rules live
  inside `packages/` and see only contracts.
- A rule MUST declare its positive fixtures explicitly; a rule without at
  least one positive fixture cannot graduate past `Draft`.

## Consequences

### Positive

- Verdict is a pure function of findings; auditable end-to-end.
- `inconclusive` is first-class, preventing silent false-clean outcomes.
- Rule deprecation is lossless via `rule_version`.
- UI type generation extends naturally to detection findings.

### Negative

- Two contracts instead of one; more surface to maintain.
- Rule lifecycle introduces a ceremony that slows the first few rules.
  This is intentional — the first rules set the pattern.

### Follow-On

- Populate the existing `packages/analysis_contracts/detection/` namespace with
  authoritative `DetectionReport` DTOs in W5.
- Extend `make test-security` to validate rule lifecycle gates (ADR 0004).
- Revisit severity and verdict rollup thresholds after the first 20 rules
  have been calibrated against real fixtures; thresholds are not sacred.
