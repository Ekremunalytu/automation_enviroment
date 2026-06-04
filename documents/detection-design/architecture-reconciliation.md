# Detection Architecture — Reconciliation & Integration Map

> Companion to [`apollyon-detection-spec.md`](apollyon-detection-spec.md). The
> spec reasons about signals; this doc maps them onto ExTrace's **real** rule
> layers, severities, gate behaviour, and the exact files/tests you touch to add
> a rule. Everything here was verified against the codebase on 2026-06-03 (the
> spec's `DOĞRULA` markers are resolved here). When code and a spec disagree,
> trust the code — and update this doc.
>
> ⛔ **Safety:** no real malware sample is ever downloaded into this repo or onto
> the host — repo fixtures are synthetic declawed canaries, live-sample validation
> is sandbox-only. Full policy: the [README](README.md) safety section.

---

## 1. There are three rule layers, not one

| Layer | Where | Input | Can it BLOCK? | Severity model |
|---|---|---|---|---|
| **In-house static** (`s*`) | [`static_runtime/rules/`](../../static_runtime/rules/) | parsed VSIX tree (`StaticAnalysisContext`) | **Yes** | per-rule `Severity` (INFO→CRITICAL) + optional `adversary_class` |
| **Semgrep static** | [`static_runtime/semgrep_rules/extrace-vsix-js.yml`](../../static_runtime/semgrep_rules/extrace-vsix-js.yml) + [`semgrep_runner.py`](../../static_runtime/semgrep_runner.py) | same VSIX tree | **No** | **hard-pinned MEDIUM/MEDIUM** for every rule |
| **Dynamic** (`a*`) | [`packages/analysis_engine/rules/`](../../packages/analysis_engine/rules/) | runtime `ActivationReport` (file/network/timing events) | n/a (post-sandbox detection) | per-rule `Severity` + `AdversaryClass` |

The spec's "Layer 1/2/3" all live in the **static** plane (in-house + semgrep);
its "Layer 4" is the **dynamic** A-series.

### Why the layer choice matters (the load-bearing constraint)

`semgrep_runner._map_result_to_finding` constructs every finding with
`severity=Severity.MEDIUM, confidence=Confidence.MEDIUM` — the `_RULE_META` table
has no severity field. So **a semgrep rule can never gate a BLOCK and never carry
HIGH/CRITICAL.** If a signal needs to *block before sandbox* or carry real
severity, it must be an **in-house s-rule** (or a dynamic a-rule). Semgrep is the
commodity "advisory WARN" surface only.

---

## 2. The static gate truth table (ADR 0016 block-and-warn)

[`workflows/marketplace/static_analysis.py::evaluate_static_gate`](../../workflows/marketplace/static_analysis.py)
turns the finding set into ALLOW / WARN / BLOCK:

- a **CRITICAL** finding → **BLOCK** (job → terminal `rejected_static`, *no* sandbox);
- a **HIGH** finding whose `rule_id` ∈ `_PROMOTED_HIGH_BLOCKERS` → **BLOCK**
  (today only `{"extrace.s2.typosquat"}`);
- otherwise any HIGH / MEDIUM / LOW → **WARN** (sandbox proceeds, warnings ride
  in the combined bundle);
- no findings, or only INFO → **ALLOW**.

So to make a signal *block*, you either set `severity=CRITICAL` or set
`severity=HIGH` **and** add its `rule_id` to `_PROMOTED_HIGH_BLOCKERS`. Changing
that frozenset is a **gate-policy change** — get explicit sign-off before doing
it (it can reject real extensions before they ever run).

---

## 3. The adversary taxonomy is A1–A7 (`AdversaryClass`, ADR 0003)

Defined in [`detection/enums.py`](../../packages/analysis_contracts/detection/enums.py);
current rule mapping (dynamic plane):

| Class | Rule | A5 note |
|---|---|---|
| A1 | `extrace.a1.credential_read_then_network` | |
| A2 | `extrace.a2.startup_network_beacon` | |
| A3 | `extrace.a3.typosquat` | |
| A4 | `extrace.a4.workspace_exfil` | catches apollyon B1 (read → network exfil) |
| **A5** | `extrace.a5.workspace_file_tamper` | ✅ **added this branch** — read → in-place rewrite (clipper/integrity); A4's integrity twin |
| A6 | `extrace.a6.startup_ui_prompt` | |
| A7 | `extrace.a7.blacklisted_domain` | |
| **A8** | `extrace.a8.reverse_shell` | ✅ **added this branch** — runtime shell spawn + outbound socket (securezeron reverse-shell class); static twin `extrace.s10.reverse_shell`. New `AdversaryClass` value (enum + generated TS DTO + fixture-hygiene set). |

**Static vs dynamic attribution split (verified):** in-house static rules carry
`adversary_class=None` (they report a *capability / IOC surface*, e.g. `s5`,
`s8`); adversary-class *attribution* belongs to the dynamic a-rules (e.g. `a4` →
`AdversaryClass.A4`). Keep new static IOC rules class-less.

**Categories** are validated strings (`finding.py::_CATEGORY_PATTERNS`): only
`attack.T####`, `extrace.ext.*`, `extrace.host.*` are accepted. Static-ext rules
use `extrace.ext.*`; dynamic host rules use `extrace.host.*`.

---

## 4. Apollyon behaviour → layer → rule → status

| Spec signal / behaviour | Layer | Rule id | Status |
|---|---|---|---|
| S1 webhook IOC | in-house static | `extrace.s8.exfil_webhook` | ✅ **shipped + verified** (this branch) |
| S2 crypto-address awareness | in-house static | `extrace.s9.crypto_address_scan` | ✅ **shipped + verified** (this branch) |
| S1 webhook IOC (commodity echo) | semgrep | *(new `discord_webhook` etc.)* | ⬜ next |
| S4 auto-trigger→sink co-occurrence | in-house static | *(new co-occurrence rule; next free `sN` — `s10` is now reverse_shell)* | ⬜ planned |
| S5 content→network taint | semgrep (taint) | *(new; intra-file; `--pro` for interproc)* | ⬜ planned |
| S5 content→network (runtime) | dynamic | `extrace.a4.workspace_exfil` | ✅ exists (catches B1) |
| S6 crypto clipper (regex→applyEdit/save) | semgrep (taint) | *(new)* | ⬜ planned (static half) |
| B3 file-integrity rewrite (runtime) | dynamic | `extrace.a5.workspace_file_tamper` | ✅ **shipped + verified** (this branch) |

The integrity gap (B3) — "extension rewrites workspace files" — is now **closed on
the dynamic plane** by `extrace.a5.workspace_file_tamper` (read → in-place write).
The remaining open piece is the *static* taint half (regex match → `applyEdit` /
`save`), still a semgrep candidate.

---

## 4b. securezeron (reverse shell) behaviour → layer → rule → status

Full reasoning in [`securezeron-detection-spec.md`](securezeron-detection-spec.md);
the layer landings (all shipped this branch):

| Signal / behaviour | Layer | Rule id | Status |
|---|---|---|---|
| RS1 shell↔socket pipe (folds RS2/RS3) | in-house static | `extrace.s10.reverse_shell` | ✅ **CRITICAL → BLOCK** (first severity-CRITICAL in-house rule) |
| RS1/RS2/RS3 AST echoes | semgrep | `reverse_shell_pipe` / `reverse_shell_spawn` / `reverse_shell_ip_connect` | ✅ advisory MEDIUM/WARN |
| RS4 `*` activation | in-house static | `extrace.s1.activation_wildcard` | ✅ pre-existing (HIGH / WARN) |
| runtime shell spawn + outbound socket | dynamic | `extrace.a8.reverse_shell` | ✅ HIGH, `AdversaryClass.A8` |

`s10` is the first in-house rule to carry **CRITICAL**, so it is the first to BLOCK
before the sandbox via the §2 gate (no `_PROMOTED_HIGH_BLOCKERS` edit needed —
CRITICAL blocks automatically). Adding `A8` was a shared-contract change (enum +
generated `contracts.ts` DTO + `test_fixture_hygiene` allow-set), signed off before
the edit.

## 4c. kagema (download-cradle dropper) behaviour → layer → rule → status

Full reasoning in [`kagema-detection-spec.md`](kagema-detection-spec.md); the layer
landings:

| Signal / behaviour | Layer | Rule id | Status |
|---|---|---|---|
| DR5 sink × cradle (DR1∧DR2, one file) | in-house static | `extrace.s11.download_cradle` | ✅ **CRITICAL → BLOCK** (the second severity-CRITICAL in-house rule) |
| DR2 cradle string (cleartext echo) | semgrep | `download_cradle` → `extrace.sg.download_cradle` | ✅ advisory MEDIUM/WARN |
| runtime PowerShell spawn + outbound socket | dynamic | `extrace.a8.reverse_shell` | ✅ pre-existing — same observable; **win32-blind for this family** |

`s11` matches the *ordered* `powershell → irm/iwr/Invoke-RestMethod/Invoke-WebRequest
→ iex/Invoke-Expression` cradle ∧ a `child_process` sink **in one file**. CRITICAL,
so it BLOCKs automatically (no `_PROMOTED_HIGH_BLOCKERS` edit, no shared-contract /
enum change — **A4 already exists** and `s11` stays **class-less** per the static-IOC
convention; the A4 attribution is conceptual, documented in the spec §7). Two
reconciliations worth noting: (1) the cradle is an **ordered single-span** regex,
**not** a loose file-level AND of the four tokens — the loose form false-positives
on `GitHub.copilot-chat/dist/cli.js`, the ordered form is 0-FP across the benign
corpus (spec §4.1); (2) **no separate `a9`** — the runtime shape (PowerShell spawn +
egress) is the same observable `a8` already correlates, so a dedicated dynamic rule
would only duplicate findings (spec §4.3). For this `win32`-gated family the Linux
sandbox never fires, so the static BLOCK is the only catching layer — the concrete
case for why static+dynamic coverage must be orthogonal.

## 5. Integration recipes (exact touch-points)

### Add an in-house static rule (`s*`)

1. New module `static_runtime/rules/sN_<name>.py` (mirror `s5_network_indicators.py`:
   `iter_text_documents` → regex → `file_evidence` → `StaticDetectionFinding`; end
   with `register(Rule())`).
2. Append the module path to `_BUILTIN_STATIC_RULE_MODULES` in
   [`registry.py`](../../static_runtime/rules/registry.py) (explicit tuple — **not**
   filesystem auto-discovery).
3. Add the `rule_id` to `EXPECTED_STATIC_PRODUCTION_RULE_IDS` in
   [`tests/static_runtime/test_rule_coverage.py`](../../tests/static_runtime/test_rule_coverage.py).
4. Bump the `rules_loaded` count in
   [`tests/static_runtime/test_static_runner.py`](../../tests/static_runtime/test_static_runner.py)
   (two asserts). ⚠️ **Also** `tests/smoke/test_static_container_smoke.py` asserts
   a (currently **stale**) count — see §6.
5. Add a `tests/static_runtime/test_sN_<name>.py` (fire + silent + FP-guard cases;
   `make_context(files={...})` fixture).

### Add a semgrep rule (commodity WARN)

1. Add a `- id: <bare_id>` block to `extrace-vsix-js.yml`.
2. Add a matching `_RULE_META[<bare_id>]` entry in `semgrep_runner.py`
   (`rule_id`, `categories`, `title`, `description`, `mitigation_hint`). Severity
   stays MEDIUM/WARN no matter what the YAML says.
3. Update the id-parity test
   [`tests/security/test_semgrep_js_rules.py`](../../tests/security/test_semgrep_js_rules.py).
   (Semgrep itself runs only in the `automation_static_analyzer` container — **no
   local semgrep on this machine**, so the wheel-level fire is verified by the
   container/CI, not locally.)

### Add a dynamic rule (`a*`)

1. New module `packages/analysis_engine/rules/aN_<name>.py` (mirror
   `a4_workspace_exfil.py`: consume `ActivationReport` events → `DetectionFinding`
   with `adversary_class`); `register(RULE)`.
2. Register in `_BUILTIN_RULE_MODULES` + the roster set in
   [`tests/security/test_rule_coverage.py`](../../tests/security/test_rule_coverage.py).
3. Add a canary fixture under [`extensions/malicious/`](../../extensions/malicious/)
   (`LABEL.yaml` with `expected_detections.must_fire` + an `activation_report.json`).

---

## 6. Shipped this branch

Three **general-purpose** rules (two static + one dynamic; engine-wide scanners,
zero apollyon-specific literals in rule logic — sample IOCs live only in tests +
the spec appendix) plus the **Rules-tab UI** that surfaces them.

### `extrace.a5.workspace_file_tamper` — S6/B3 clipper (dynamic)

The integrity counterpart to A4. Fires when the **target** extension reads a
`/workspace/` file and then **writes back to the same path** (read → modify →
save) — the runtime signature of a crypto-clipper / content-rewriter, and the
dynamic counterpart of `s9`. Uses the file-event `operation` vocabulary
(`read` / `write`, normalised from inotify `CLOSE_WRITE`/`MODIFY` + strace) over
`target_file_events`. `severity=MEDIUM`, `confidence=MEDIUM`,
`categories=["attack.T1565", "extrace.host.workspace_tamper"]`,
`adversary_class=AdversaryClass.A5`. **MEDIUM, not HIGH**: the file layer sees
"read then wrote the same file" but not *what* changed, and legitimate formatters
do this too — it surfaces the integrity action for review, not a conviction.
Validated by a synthetic canary (no payload):
[`t1-a5-file-tamper-canary`](../../extensions/malicious/t1-a5-file-tamper-canary/)
(read+write same path → fires; the A4 read+network canary → silent).

### `extrace.s9.crypto_address_scan` — S2 crypto-address awareness

Fires when any extension's source recognises a wallet-address format: Base58
fragments `a-km-z` / `A-HJ-NP-Z` (near-unique to crypto → HIGH confidence), `0x`

+ 40-hex (Ethereum; the `0x` prefix is required so a 40-char SHA-1 hex regex does
**not** false-positive), or `bc1[` (bech32/SegWit — which apollyon's own regex
misses). `severity=MEDIUM`, `categories=["attack.T1565",
"extrace.ext.crypto_address_scan"]`, `adversary_class=None`. MEDIUM/WARN by design
— a genuine blockchain/wallet extension legitimately has these, so it surfaces
the capability for review/escalation rather than convicting on presence alone.

### `extrace.s8.exfil_webhook` — S1 chat-webhook IOC

- Detects Discord (`/api/webhooks/<id>/<token>`, incl. `discordapp.com` / `ptb.` /
  `canary.`), Slack (`hooks.slack.com/services/...`), Telegram
  (`api.telegram.org/bot<token>`) **ingestion-path** literals — not bare host
  mentions, so a README discord.com community link does **not** fire.
- `severity=HIGH`, `confidence=HIGH`, `categories=["attack.T1567",
  "extrace.ext.exfil_webhook"]` (T1567 = Exfiltration Over Web Service),
  `adversary_class=None`. One aggregated finding; token rides the shared
  secret-redaction path before any report/UI/log surface.
- **HIGH → WARN, not BLOCK** (deliberately not in `_PROMOTED_HIGH_BLOCKERS`):
  webhook-presence-alone shouldn't reject before sandbox; matches the spec's "S1
  alone = HIGH, escalate on co-occurrence". Promoting it is an open decision (§7).

### UI — the Rules tab now shows static *and* dynamic rules

The standalone **Rules tab** (`RulesPage.tsx` Registry) was **dynamic-only** (it
built rows from `detection.rulesExecuted`). It now builds a **unified row list** —
dynamic rules from `rulesExecuted` **plus** static rules from the static-catalog
universe + `staticReport.findings` (silent ones enumerated too) — and renders each
with a **Static / Dynamic** badge, a **stream filter** (All / Dynamic / Static),
and the `stream` field in the conditions table. Per-cell stream tags also landed
in the report-page `RuleMatrixSection`. Every catalog entry
([`ruleCatalog.ts`](../../ui/src/features/reports/ruleCatalog.ts)) gained a richer
`detail` paragraph (rendered in the rule dialog / expanded row); `s8`, `s9`, `a5`
were added to the catalog.

### Policy: `s1.activation_wildcard` LOW → HIGH

An always-on `*` activation is a no-user-intent foothold that amplifies every
other capability — too load-bearing for LOW. Raised to **HIGH** (rule + catalog +
test). Still **WARN, not BLOCK** (not in `_PROMOTED_HIGH_BLOCKERS` — many
legitimate extensions declare `*`).

### Verification

- Python: `pytest tests/static_runtime/ tests/security/` green; ruff + mypy clean.
  Static registry = **12** rules (s1–s9 incl. multi-rule modules), dynamic = **8**
  (a1–a7 + demo, a5 included). *(securezeron branch then grew this to **13** static
  / **9** dynamic via `s10` + `a8` — see §4b; the container smoke count was bumped
  6 → 13 to match. kagema then grew static to **14** via `s11` — see §4c; smoke
  count 13 → 14.)*
- UI: `tsc -b` clean, `vitest run` **110 passed** (incl. a new static-visibility
  test), `npm run build` ✓.
- **Browser-verified** live in the Rules tab (ui-dev :5173 against an
  `ms-python.python` report): static + dynamic rows both render with Static/Dynamic
  badges, the stream filter works, s8/s9/a5 present, `detail` text renders on
  expand. (Semgrep-layer fire still needs the container.)

Files: rules [`a5_workspace_file_tamper.py`](../../packages/analysis_engine/rules/a5_workspace_file_tamper.py)
· [`s8_exfil_webhook.py`](../../static_runtime/rules/s8_exfil_webhook.py)
· [`s9_crypto_address_scan.py`](../../static_runtime/rules/s9_crypto_address_scan.py);
tests `test_a5_*` / `test_s8_*` / `test_s9_*` + the RulesPage static-visibility
test; registry + roster/count test edits per §5; the UI files above.

---

## 7. Open decisions (need your call)

1. **Promote s8 to a blocker?** Add `extrace.s8.exfil_webhook` to
   `_PROMOTED_HIGH_BLOCKERS` so a hardcoded chat-webhook *rejects before sandbox*?
   (Gate-policy change — defaulted **off**.)
2. **Semgrep commodity echo** of the webhook/crypto IOCs (MEDIUM WARN, double
   evidence) — worth the duplicate, or keep IOCs in-house only?
3. **Static clipper half** — add the semgrep taint rule (crypto-regex match →
   `applyEdit` / `save`) to complement the dynamic `a5`? (Static side of B3.)
4. **Stale smoke count** — `tests/smoke/test_static_container_smoke.py` asserts
   `rules_loaded == 6`, already wrong before this work (real static count is now
   **12**). Container-gated + can't verify locally, so left untouched (pre-existing
   drift). Bump it, or reconcile on the next container run?

**Resolved this branch:** the A5 clipper rule (shipped, §6) and the "fixture in
repo" question — settled by policy: **no real sample in repo**, only synthetic
canaries; live-sample validation is sandbox-only (README safety section).
