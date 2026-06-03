# Detection Design — custom rule development

`Branch: security-development` · `Started: 2026-06-03`

Working area for **custom detection-rule development**: per-malware-class design
specs, the map from those specs to ExTrace's real rule layers, and a living
status board. This is an **iterative** effort — the owner writes tests and feeds
back; rules and these docs grow per cycle. This directory is intentionally
self-contained and does **not** drive the canonical static-lane docs (those
reconcile on the owner's cadence, post-merge).

---

## ⛔ SAFETY — never bring live malware into this repository

> **Real malicious extension samples are NEVER downloaded, committed, or stored
> anywhere in this repository or on the developer host.** Not in `extensions/`,
> not in `documents/`, not in a scratch dir, not "temporarily".
>
> - **Repo fixtures are SYNTHETIC, declawed canaries only** — hand-authored
>   manifests / `activation_report.json` files that *describe* a behaviour shape
>   (see [`extensions/malicious/`](../../extensions/malicious/), all
>   `kind: internal_canary`). They contain no working payload, no live C2
>   endpoint, no real wallet address, no executable malware.
> - **Live samples are analysed ONLY inside the isolated sandbox** — the
>   `automation_executor` / `automation_static_analyzer` containers
>   (`network_mode: none`, `cap_drop: [ALL]`, disposable). A sample enters the
>   sandbox through the analysis pipeline and is destroyed with the container; it
>   never lands on the host filesystem or in git.
> - **IOC strings in these docs are reference-only** (attribution + regression
>   anchors). A webhook URL or address in the appendix is text in a doc, not a
>   fetched artefact, and must never be resolved, executed, or used to pull the
>   real sample down.
>
> Provenance fields (upstream repo URLs, hashes) exist for *attribution and
> citation*, not as a fetch instruction. If a rule needs validating against a
> real sample, that happens in the sandbox — full stop.

---

## Docs

| Doc | Purpose |
|---|---|
| [`architecture-reconciliation.md`](architecture-reconciliation.md) | **Read first.** The three rule layers, the ADR-0016 gate truth table, the A1–A7 taxonomy, and the exact files/tests to add a rule in each layer. |
| [`apollyon-detection-spec.md`](apollyon-detection-spec.md) | Detection design spec for the `apollyon` Discord-webhook infostealer class: behaviour breakdown, signal catalog, escalation matrix, evasion limits, IOC appendix. |

## Design principle: general, not sample-specific

Rules are **engine-wide scanners**, not apollyon signatures. Every rule here runs
over *every* extension's source/runtime in the normal pipeline and asks a generic
question — "why does **any** extension hardcode a Discord webhook?", "why does
**any** extension carry crypto-address regexes?" — never "is this byte-for-byte
apollyon?". Sample-specific IOCs live only in the spec's regression appendix and
in test inputs; **never** in rule logic. apollyon is the *design driver*, not the
*target*. New rules must keep this property: match a behaviour/capability class,
not a known sample.

## The three layers (one-liner)

- **In-house static** (`static_runtime/rules/s*`) — VSIX-tree rules; can carry any
  severity and can **BLOCK** before the sandbox.
- **Semgrep static** (`static_runtime/semgrep_rules/`) — commodity dataflow rules;
  **hard-pinned MEDIUM/WARN**, never blocks.
- **Dynamic** (`packages/analysis_engine/rules/a*`) — behavioural rules over the
  runtime `ActivationReport`; carry `AdversaryClass` attribution.

## Shipped so far (this branch)

Three **general** detection rules + the UI to surface them. None hardcodes an
apollyon literal; all scan every extension.

| Rule | Layer | What it catches | Severity |
|---|---|---|---|
| [`extrace.s8.exfil_webhook`](../../static_runtime/rules/s8_exfil_webhook.py) | static | Hardcoded Discord/Slack/Telegram **webhook** ingestion endpoint (the exfil channel) | HIGH (warn) |
| [`extrace.s9.crypto_address_scan`](../../static_runtime/rules/s9_crypto_address_scan.py) | static | Source recognises **crypto-address** formats (Base58/ETH/bech32) — clipper capability | MEDIUM (warn) |
| [`extrace.a5.workspace_file_tamper`](../../packages/analysis_engine/rules/a5_workspace_file_tamper.py) | dynamic | Workspace file **read then rewritten in place** at runtime — clipper/integrity | MEDIUM |

UI ([`ruleCatalog.ts`](../../ui/src/features/reports/ruleCatalog.ts) +
[`RulesPage.tsx`](../../ui/src/features/rules/RulesPage.tsx)): the **Rules tab now
lists static *and* dynamic rules** (was dynamic-only), each with a **Static /
Dynamic** badge and a stream filter; every catalog rule carries a richer `detail`
description. Detail in the reconciliation doc §6.

Policy tweak: `extrace.s1.activation_wildcard` raised **LOW → HIGH** (an always-on
`*` foothold is too load-bearing for LOW; warns, never blocks).

## Status board — apollyon class

| Signal | Layer | Rule id | Status |
|---|---|---|---|
| S1 chat-webhook IOC | in-house static | `extrace.s8.exfil_webhook` | ✅ shipped + verified |
| S2 crypto-address awareness | in-house static | `extrace.s9.crypto_address_scan` | ✅ shipped + verified |
| S5 content→network (runtime) | dynamic | `extrace.a4.workspace_exfil` | ✅ exists |
| S6 / B3 crypto clipper (integrity) | dynamic | `extrace.a5.workspace_file_tamper` | ✅ shipped + verified |
| S1 webhook (commodity echo) | semgrep | *tbd* | ⬜ next |
| S4 auto-trigger→sink co-occurrence | in-house static | *tbd (`s10`)* | ⬜ planned |
| S5 content→network (taint) | semgrep | *tbd* | ⬜ planned |

## Iteration loop

1. Owner writes / runs a test against a fixture (or a live sample **in the
   sandbox** — never on the host).
2. Owner feeds back the result (fired / silent / FP / miss).
3. Rule(s) are added or tuned in the right layer (see reconciliation §5).
4. This board + the relevant spec are enriched; tests stay green.

## Verify locally (what runs without the container)

```bash
.venv/bin/python -m pytest tests/static_runtime/ tests/security/ -q  # static + dynamic rules
.venv/bin/ruff check static_runtime/rules/ packages/analysis_engine/rules/
npx --prefix ui tsc -b && npx --prefix ui vitest run                 # UI types + tests
```

Semgrep and the full VSIX pipeline run only in the `automation_static_analyzer`
container (`make static-up` / CI) — there is no local semgrep on the dev machine.
