# ADR 0015 — Sandbox-Evasion Defense Policy (Taxonomy + Roadmap Draft)

- Status: Accepted (Draft Policy — taxonomy stable; defense
  implementation deferred to W23+)
- Date: 2026-05-28
- Authors: ekrem + Claude
- Driving phase: W22-4 — `[GOAL sandbox-evasion-defense-mvp]` —
  promotes the ADR 0002 §3 "advanced sandbox evasion" out-of-scope
  bucket into a scoped W23+ implementation lane; unblocks W22-5
  `[GOAL sandbox-evasion-canary-fixture]` synthetic detection
  fixture
- Related: ADR 0001 (single-host appliance), ADR 0002 (threat
  model), ADR 0013 (container isolation baseline)

## Context

ADR 0002 §3 ("Explicitly Out-of-Scope Capabilities") declared
**advanced sandbox evasion** out of scope for the PoC phase:

> "Playwright CDP fingerprinting, detection of harness extension
> presence, detection of the analyzer via `navigator.webdriver` or
> equivalent."

The required response when such evasion is encountered is
`inconclusive`, not a false-negative-claiming `clean`. That posture
was correct for the platform-maturity window covered by W8-W21:
the program could not reliably detect evasion attempts, so silently
classifying them as clean would have understated risk.

Two W22-window facts now make a scoped re-evaluation timely:

1. **Coverage breadth is at the hard-tier boundary** (W22-1, W22-2).
   With chat closed, the last "missing" capability in
   `coverage_summary.missing_capabilities` reaches 0. The next
   limiting factor for analysis fidelity is no longer breadth — it
   is targeted adversarial behavior.
2. **Container hardening (W22-6) *would* reduce the side-channel surface — but it was deferred.**
   `read_only: true` + a custom seccomp filter would together remove some of
   the cheapest evasion probes (process introspection via `/proc`,
   syscalls used by `unshare`/`mount` detection). W22-6 was deferred-to-user
   (now post-v1.0 Stream 8 `[GOAL container-hardening-ratchet-down]`); today
   only `cap_drop: [ALL]` + `no-new-privileges: true` are enforced.

ADR 0002 §3's "follow-up ADR" mechanism is the entry point. This
ADR is that follow-up. **It does not yet add runtime defenses; it
establishes the taxonomy that W22-5 canary fixtures + W23+
implementation will both build against.**

## Decision

### Sandbox-Evasion Pattern Taxonomy (stable from this ADR onward)

Five pattern families capture the realistic evasion surface for the
marketplace analyzer. Each family has a stable short-name and a
documented detection / suppression strategy. Names are
load-bearing — `tests/security/test_sandbox_evasion_canary.py`
(W22-5) references them; future iterations must update this ADR if
the names change.

| # | Family | Short-name | Realistic probe example | Suppression / detection surface |
|---|---|---|---|---|
| E1 | Webdriver presence interrogation | `webdriver_presence` | Extension reads `navigator.webdriver`; if `true` → bails | Playwright launch flag + `page.addInitScript` overriding `navigator.webdriver` to `false`; canary fixture exercises both raw read + getter-trap variants |
| E2 | CDP / automation-runtime fingerprinting | `cdp_fingerprint` | Extension probes `window.cdc_*`, `window.callPhantom`, CDP-specific Runtime properties | `page.addInitScript` deletes the well-known CDP-leak globals before any extension JS runs |
| E3 | Headless/timing-based environment probes | `timing_probe` | Extension samples `performance.now()` jitter or measures `Date.now()` granularity; headless environments often have detectable rendering cadence | Passive — do NOT attempt full masking; the W22-6 seccomp + cgroup posture pins timing variance closely enough that synthetic probes can be benchmarked against a "real-host" baseline. Detection record + classification, not masking. |
| E4 | UA / platform identity interrogation | `platform_identity` | Extension reads `navigator.userAgent`, `navigator.platform`, `process.platform`, or VS Code's `os.platform()` looking for analyzer-characteristic strings | `page.setExtraHTTPHeaders` + `page.addInitScript` override `userAgent` and `platform` to match a representative real-user macOS/Linux profile; VS Code's `os` module values come from the host so the container's `uname` shape must match a "real user" profile (Debian + glibc, NOT a custom analysis label) |
| E5 | Process / filesystem introspection | `process_introspection` | Extension reads `/proc/*/cmdline` or `/proc/self/status` for analyzer-characteristic process names; checks for `playwright`, `xvfb`, `analyzer`-prefixed paths | Largely covered by W22-6 `read_only` + custom seccomp + `cap_drop:[ALL]`; the residual `/proc` visibility is bounded. Defense placement: container layer (W22-6 baseline) + Playwright launcher argv hygiene |

### Policy Stance per Family

For each family, the policy stance defines whether the harness
**suppresses** the signal (the extension's probe returns
analyzer-indistinguishable values), **detects** the probe (the
analyzer records that the extension attempted evasion and labels
the artifact `suspicious_evasion`), or **passively observes**
(neither suppression nor flagging — used when the cost of either is
higher than the value).

| Family | Stance | Rationale |
|---|---|---|
| E1 `webdriver_presence` | **Suppress + Detect** | Cheapest evasion surface and one of the strongest "I'm being analyzed" tells — masking is high-value. Pairing with detection (count of `navigator.webdriver` reads in the run) captures both raw and getter-trap variants. |
| E2 `cdp_fingerprint` | **Suppress + Detect** | Suppress via init script; detect via Playwright DOM event listeners + a global-property access counter injected before any extension JS. |
| E3 `timing_probe` | **Passively observe + Detect** | Full masking requires intercepting `performance.now()` / `Date.now()` per-call; this is complex, brittle, and risks normal-application breakage. Better: classify the probe as suspicious behavior and route to `inconclusive` analyst review. |
| E4 `platform_identity` | **Suppress + Detect** | Suppression is a Playwright launch concern; detection is a static-marker scan of probe targets. |
| E5 `process_introspection` | **Defense-in-depth (containment)** | W22-6 ratchet-down already restricts `/proc` visibility via cap_drop + seccomp; the residual surface is small enough that probe attempts become low-yield. Detection record only. |

### Defense Surface Placement (where each lives)

Each family's defense (suppression or detection) lives at the
narrowest sensible architectural layer. The same layer also owns
the regression test for that defense.

| Family | Layer | Owning module | W22-5 canary entry-point |
|---|---|---|---|
| E1 | Playwright launcher + page init | `executor/flows/playwright/launcher.py` + `executor/flows/playwright/page_init/webdriver_mask.js` (W23+ new) | `tests/security/test_sandbox_evasion_canary.py::test_webdriver_presence_probe_is_recorded` |
| E2 | Playwright page init | `executor/flows/playwright/page_init/cdp_mask.js` (W23+ new) | `tests/security/test_sandbox_evasion_canary.py::test_cdp_fingerprint_probe_is_recorded` |
| E3 | Detection-only — analysis_planner stimulus dispatch | `packages/analysis_planner/evasion_signals.py` (W23+ new) — passive recorder | `tests/security/test_sandbox_evasion_canary.py::test_timing_probe_is_recorded_without_masking` |
| E4 | Playwright launcher + UA / platform overrides | `executor/flows/playwright/launcher.py` profile shape | `tests/security/test_sandbox_evasion_canary.py::test_platform_identity_probe_is_recorded` |
| E5 | Container layer (W22-6 already baselined) + Playwright argv hygiene | `docker-compose.yml` (W22-6 covers) + `executor/flows/playwright/launcher.py` argv audit | `tests/security/test_sandbox_evasion_canary.py::test_process_introspection_is_constrained_by_container` |

W22-5 canary fixture lands ONLY the synthetic probes that exercise
each family **from the analyzer-side observer's perspective** (i.e.,
the fixture simulates the data the analyzer would see if an
extension performed the probe; it does NOT yet exercise the
suppression itself — that is W23+ scope when the suppression code
lands).

### Security Posture (what we will NOT do under this ADR)

- **No remote model / cloud heuristics for evasion classification.**
  The same AGENTS.md no-external-services rule that ADR 0014 cited
  applies here. Evasion detection is local-only: pattern matching +
  per-family probe counters + heuristic thresholds.
- **No active deception beyond the masking listed above.** The
  harness does not synthesize fake `/proc` content, fake interactive
  user mouse traces, or fake telemetry endpoints — those raise the
  threat model to V2 architectural changes (full host-virtualization
  layer) that are out of scope for the PoC + immediate follow-on
  windows.
- **No engagement with mouse trail / focus pattern detection** in
  this ADR. Some commercial evasion-aware malware checks for
  human-pattern interaction signatures (cursor jitter,
  focus-change cadence). Mitigating that requires synthetic-input
  generation tuned to per-locale human variance — out of scope
  here; revisit when a real-world fixture demonstrates the need.

### W19-X Marker Channel Conformance

When W23+ implements the runtime detection paths (E1, E2, E4
detection; E3, E5 record-only), the new evasion-event markers MUST
route through the existing reserved `"ExTrace Harness"`
OutputChannel via `emitHarnessEvent` (ADR 0010 + W19-X Bug B
paterni). A new marker family `evasion_signal` with `phase` ∈
{`probed`, `suppressed`, `recorded`} is the foreseen shape; final
schema is W23+ scope.

### Engine Compatibility

- Playwright `page.addInitScript`, `page.setExtraHTTPHeaders`,
  launch-arg overrides — all stable in the currently pinned
  Playwright version (`pyproject.toml` lock).
- VS Code `engines.vscode` constraint — not touched by this ADR
  (no new VS Code API surfaces; all defenses live below the
  Extension Host).
- `docker/seccomp.json` (W22-6) — **deferred, not yet shipped** (no
  `seccomp.json` exists; the ratchet-down is post-v1.0 Stream 8). Until it
  lands, E5 relies only on `cap_drop: [ALL]` + `no-new-privileges: true`; the
  `/proc`-visibility hardening is planned, not in force.

## Consequences

### Positive

- Closes the ADR 0002 §3 "advanced sandbox evasion" out-of-scope
  bucket as a deliberate W23+ lane rather than an open gap. The
  promotion path ("Out-of-scope classes can be moved in-scope via
  a follow-up ADR" — ADR 0002 §3 final paragraph) is exercised.
- Establishes a stable taxonomy that W22-5 canary fixtures can
  build against today, even before W23+ runtime defenses land.
  This decouples test-side scaffolding from implementation
  scheduling.
- Names the load-bearing modules for W23+ implementation up-front,
  so iteration planning can sequence E1+E2 (Playwright page init
  scripts) ahead of E3+E5 (signal recording infrastructure)
  without re-litigating where each defense lives.
- Documents what the program will explicitly NOT do (active
  deception, mouse-trail synthesis, remote-model classification)
  so future scope creep surfaces at ADR amendment, not at
  implementation review.

### Negative

- A sophisticated evasion-aware extension that combines E1 + E3 +
  E5 with a probabilistic trigger threshold could still bypass
  detection during W23+ implementation. ADR 0002 §3 declared
  `inconclusive` the correct response; that classification remains
  the documented out for residual evasion until V2 architectural
  hardening lands.
- The W22-5 canary fixture is "observer-side only" — it exercises
  the taxonomy but cannot validate suppression effectiveness until
  W23+ ships the actual suppression code. The W22-5 acceptance
  signal is "the analyzer correctly records that a probe occurred",
  not "the probe was suppressed".
- Engine pinning becomes more load-bearing — a future Playwright
  upgrade that changes `addInitScript` semantics could silently
  weaken E1/E2 defenses. Mitigation: the W23+ implementation must
  add Playwright-version pin invariants alongside the new
  page-init scripts.

### Operational notes (W22-5 canary acceptance)

W22-5 lands the synthetic-probe fixture at
`tests/security/test_sandbox_evasion_canary.py`. Each test exercises
one family by simulating the data flow an analyzer would see when
the corresponding evasion probe runs against the analyzer-managed
Playwright surface. The fixture acceptance bar:

- 5 tests, one per family (E1..E5).
- `make test-security` count: 220 → 221 (one new file with 5
  parametrized cases counts as +1 at the file level; the actual
  case count is bumped in the W22-5 implementation commit).
- Each test asserts on the taxonomy short-name (`webdriver_presence`,
  `cdp_fingerprint`, …) so this ADR's taxonomy IS the public
  contract.

## Implementation Roadmap (W23+)

This ADR is **Accepted as a Draft Policy**: the taxonomy + policy
stance + defense surface placement are stable; the runtime
implementation lands in W23+ as named:

- **W23+ first sub-iter** — Playwright page-init scripts for E1
  (`webdriver_mask.js`) + E2 (`cdp_mask.js`); launcher integration;
  E1 + E2 detection counters in `evasion_signals.py`.
- **W23+ second sub-iter** — E3 timing-probe signal recorder
  (passive); E4 platform identity launcher overrides.
- **W23+ third sub-iter** — E5 container-layer audit (validate
  W22-6 baseline still meets the placement claim above; argv
  hygiene in `launcher.py`).
- **Future ADR (W24+ or later)** — V2 architectural decision on
  active deception layers (mouse trail synthesis, full host
  virtualization). Not committed by this ADR.

## Alternatives Rejected

**Option A — Defer the whole lane to V2 (no W22-4 ADR).** Would
leave ADR 0002 §3 as the only reference, with no scoped path to
in-scope promotion. **Rejected** because W22-5 depends on a stable
taxonomy contract for its synthetic probes; without ADR 0015, the
canary fixture's short-names become arbitrary and would re-litigate
at every refactor.

**Option B — Implement E1 + E2 suppression in W22-4 itself
(combine ADR + first runtime cut).** Would deliver immediate
defense against the cheapest probes. **Rejected** because Playwright
page-init scripts touch the launcher hot path and a bug there
silently affects every analyze run; per the W22 overlap-aware
execution order (low-risk first, runtime-touching iters last), the
launcher edit belongs in a dedicated W23+ sub-iter with its own
live-run smoke gate. ADR 0015 captures the taxonomy without
introducing runtime risk.

**Option C — Detect-only across all families (no suppression
anywhere).** Would record evasion attempts but not blunt them.
**Rejected** for E1 + E2: those probes are so cheap to evade that
declining to suppress them sacrifices the analyzer's effective
threat surface against any adversary who can spend five minutes on
StackOverflow. Suppression is the higher-leverage choice for E1 +
E2; detection-only is correct for E3 + E5 where suppression cost
exceeds value.

**Option D — Mark each family as `must-suppress` uniformly.**
Would commit to active masking everywhere. **Rejected** because E3
timing probes require per-call instrumentation that risks normal
extension breakage (extensions legitimately measure timing for
profiling). Per-family stance differentiation matches the actual
cost/value gradient.

## References

- `documents/adrs/0002-threat-model.md` §3 — original out-of-scope
  declaration that this ADR promotes.
- `documents/adrs/0001-single-host-appliance.md` — single-host
  appliance constraint that frames why container-layer defenses
  (E5) are load-bearing.
- `documents/adrs/0010-extrace-executor-logger-consolidation.md` —
  reserved `"ExTrace Harness"` OutputChannel route reused for
  W23+ evasion markers.
- `documents/adrs/0013-container-isolation-baseline.md` —
  container hardening that already constrains E5 surface; W22-6
  ratchet-down extends it.
- `documents/adrs/0014-chat-and-language-model-tool-policy.md` —
  immediately prior W22 ADR; established the "stable APIs only,
  no external services" pattern reused here.
- Playwright `page.addInitScript` API reference — `https://
  playwright.dev/docs/api/class-page#page-add-init-script`.
- AGENTS.md — no-external-services project rule referenced under
  §Security Posture.
