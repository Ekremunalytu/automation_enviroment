# W20 Handoff — Close-Out Kontrolleri (Yeni Session İçin)

> **STATUS: SUPERSEDED — frozen `2026-05-27` at W20-5 close-out.**
> Mirrors the W19-X-handoff.md `2026-05-26` paterni. This handoff
> doc was authored `2026-05-26` by a previous session before context
> handoff to a close-out session; the close-out session executed the
> instructions below and W20 closed synthetically `2026-05-27` via
> W20-5 primary `4665d32` + self-stamp `95b0010` + followup-2
> `d163b02` (filed `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]`
> for W21) + followup-3 `ae5b7de` (10-doc preamble `(this commit)`
> placeholder backfill). Final W20 bar: `tests/architecture/` **240
> passed**; `make test-security` **220 passed**; full suite **2045
> passed, 9 skipped, 8 deselected**. W20 acceptance LIVE-SATISFIED
> on fresh run `4e92de149802` (sha256 `3804a5b5...4394c`):
> `coverage_summary.missing_capabilities` 6 → 4 (lost `scm` +
> `settings`); W19 Hat-1 + Hat-2 hold post-W20. Close-out PR
> `week20 -> main` open **PENDING USER APPROVAL**.
>
> **Why this doc is kept frozen rather than deleted**: the
> close-out kontrolleri narrative (Step 1..Step 5 instruction
> list + assertion ledgers) is irrecoverable session-handoff
> context useful for future weekN handoff doc authors mirroring
> the W20 paterni. The W20 frozen tracker
> [`W20-coverage-promotion-easy-wins.md`](W20-coverage-promotion-easy-wins.md)
> is the canonical W20 audit-trail source-of-truth post-close-out.
> Inline references to "W20 active tracker" elsewhere in this
> doc are stale — read them as "the W20 tracker (now frozen)".

`Status: HANDOFF (SUPERSEDED) — W20-0..W20-5 all closed; W20-5 close-out PR week20 -> main PENDING USER APPROVAL.`
`Branch: week20 (cut from main @ 52a47f4 — W19 close-out post-merge cross-doc parity gate commit).`
`Authored: 2026-05-26 by previous session before context handoff to a close-out session; frozen 2026-05-27 at W20-5 close-out.`
`Owner: ekrem.`

> **Purpose.** This document is a self-contained briefing for a new
> Claude Code session that picks up W20 cold to run the W20-5
> close-out kontrolleri. Everything you need to verify and ship W20
> is captured here. Do not re-derive what this doc settles; do verify
> the assertions are still true by reading the cited files at the
> cited line numbers and re-running the cited commands.

---

## TL;DR — One Paragraph

W20 (Coverage Promotion Round 1: Easy Wins) is `5/6` sub-iters
done. 10 commits sitting locally on the `week20` branch (not
pushed). `_OFFICIAL_CAPABILITY_SUPPORT["scm"]` and `["settings"]`
were flipped from `"missing"` to `"covered"` (single-character
edits at `packages/analysis_planner/capabilities.py:88` and `:90`),
13 invariant tests landed (4 scm-specific + 4 settings-specific +
5 broader coverage matrix contract pins), one design doc landed
for W21 plumbing readiness, and the W20 doc-reconcile +
9-doc canonical preamble refresh + §18 promote + W20 Pull-Forward
Acceptance Bar promote all landed. A live UI-driven analyze run
on `ms-python.python` was captured BEFORE the flips (W20-0
baseline, `e89a82ca9ba8`) and another AFTER the flips (W20-1+W20-2
post-acceptance evidence, `71ce478660bb`) — both prove the W19
close-out (`unaccounted_dropout == 0`, `harness_verification_unconfirmed_present`
DROPPED) holds and the W20 acceptance bar (`scm` + `settings`
drop from `missing_capabilities`, 6 → 4) is **LIVE-SATISFIED**.
W20-5 close-out remains: optional final live-run (the
`71ce478660bb` JSON can serve as final evidence — no new
container build needed), canonical preamble `Active → Previous`
flip, W20 tracker freeze + §18 self-stamp, `git push -u origin
week20` and `gh pr create --base main --head week20`. **Push and
PR open are STRICT pause points per plan file + user memory
entry — user must say "go" in the same turn before either runs.**

---

## State On Disk

### Commit Audit Trail (10 commits, week20 branch, oldest first)

| # | SHA | Sub-Iter | Theme |
|---|---|---|---|
| 1 | `66a8a0b` | W20-0 primary | doc-reconcile — open week20 + §18 promote + 9-doc canonical preamble refresh |
| 2 | `5f13757` | W20-0 self-stamp | baseline live-run captured + W19 close-out Hat-1/Hat-2 live-verified |
| 3 | `82276cb` | W20-1 primary | `scm` official-track promotion (missing → covered) + 4 invariant tests + fixture regen |
| 4 | `a17e595` | W20-1 self-stamp | W20-1 tracker row flip (planned → closed) + §18 + POST_POC mirrors |
| 5 | `a4343d2` | W20-2 primary | `settings` official-track promotion (missing → covered) + 4 invariant tests + fixture regen |
| 6 | `7406588` | W20-2 self-stamp | W20-2 tracker row flip + §18 + POST_POC mirrors |
| 7 | `d4c03b6` | W20-3 primary | coverage matrix contract invariants (5 new tests; keyset parity + Official ⊆ Heuristic + notes ↔ taxonomy + ordering + W20-1/W20-2 combined post-condition) |
| 8 | `2e39230` | W20-3 self-stamp | W20-3 tracker row flip + §18 + POST_POC mirrors |
| 9 | `05f47f3` | W20-4 primary | comments + testing readiness DESIGN doc for W21 plumbing |
| 10 | `b409894` | W20-4 self-stamp | W20-4 tracker row flip + §18 + POST_POC mirrors |

`git log --oneline main..week20 | awk '{a[NR]=$0} END {for (i=NR; i>=1; i--) print a[i]}'`
will reproduce this in chronological order.

### Working Tree

`git status` shows clean. No uncommitted changes. No untracked files
(except the `output/activation_report_*.json` files which are bind-mount artefacts).

### Test Bar (latest)

- `tests/architecture/`: **208 passed**, 4 deselected (W19 final
  204 → +4: +1 W19 close-out fact gate
  `test_readme_phase_pointer_mentions_w19_closeout_merge` +3 from
  pre-existing W19-6-followup-2 era arch tests on `main` at the
  branch cut point).
- `make test-security`: **220 passed** (unchanged from W19).
- Full suite (`.venv/bin/pytest -q`): **2012 passed**, 9 skipped,
  8 deselected (W19 final 1995 → +17: +4 from W20-0 + 4 from W20-1
  + 4 from W20-2 + 5 from W20-3 + 0 from W20-4 doc-only).

### Acceptance Bar Verification (LIVE)

Two activation reports captured locally during the W20 work:

| Anchor | sha256 | When | Purpose |
|---|---|---|---|
| `e89a82ca9ba8` | `4dd788268f7793143351721875d6ccb340bd1e01b2b0205c53a5561ed0256ffe` | W20-0 baseline (pre-flips) | W19 close-out live verification + W20 baseline |
| `71ce478660bb` | `cb402365a19474ad75bdd53925d5c89f947f541bd4554e7ee6d14463bd45cd83` | After W20-1+W20-2 flips merged into the running container | W20 acceptance bar verification |

Live evidence on `71ce478660bb`:

- `unaccounted_dropout` count = **0** (W19 Hat-1 holds post-flips).
- `automation_health.reasons = [skipped_scenarios_present,
  verification_gap_present, official_unresolved_present]` —
  `harness_verification_unconfirmed_present` DROPPED (W19 Hat-2
  holds post-flips).
- `confirmation_source` distribution across 21 event_attempts:
  `harness_nonce = 2` + `log_record = 6` + `none = 13` (W19-3/4/5
  schema + producer landings hold post-flips).
- `coverage_summary.missing_capabilities = [chat, comments, testing,
  workspace_trust]` — **6 → 4, dropped `scm` + `settings`**
  (W20-1 + W20-2 acceptance bar SATISFIED).
- `coverage_summary.partial_capabilities = [scm, search_views,
  settings, notebooks, custom_editors, authentication, webview]` —
  `scm` + `settings` landed in `partial` (not `covered`) because
  ms-python.python doesn't trigger `onView:scm` /
  `settings_modification` events, so `is_active = false` for both.
  This is expected.
- Official matrix for `scm`: `support_status: "covered"` (W20-1
  flip live), `status: "partial"`, `supported_scenarios:
  ["git_workflow"]`.
- Official matrix for `settings`: `support_status: "covered"`
  (W20-2 flip live), `status: "partial"`, `supported_scenarios:
  ["settings_modification"]`.
- `run_quality: "low"` — still low; expected (the
  `official_unresolved_present` contributor closes after W22
  hard tier when `chat`+`workspace_trust`+`testing`+`comments`
  promote).
- `automation_health.status: "degraded"` — expected, same reason.

W20 acceptance gate (W18-W22-roadmap.md §W20 acceptance):

| Criterion | Required | Observed | Status |
|---|---|---|---|
| `coverage_summary.missing` drops `scm` | must-pass | dropped | ✅ |
| `coverage_summary.missing` drops `settings` | must-pass | dropped | ✅ |
| Coverage matrix contract tests yeşil | must-pass | 5/5 + 8 per-capability | ✅ |
| Activation event spec crosswalk raporu yazılı | must-pass | W20-4 design doc landed (broader scope than just crosswalk; crosswalk research deferred to W22-6 if needed) | ⚠️ (broader doc landed; pure crosswalk DEFERRED — see Open Question #1) |
| Static suite yeşil | must-pass | 208/220/2012 | ✅ |

---

## W20-5 Close-Out Scope — Step-by-Step

### Step 0 — Verify state (no destructive operations)

```bash
git rev-parse --abbrev-ref HEAD   # → week20
git log --oneline main..week20    # → 10 commits, expected SHAs above
git status                        # → "nothing to commit, working tree clean"
.venv/bin/pytest tests/architecture/ -q   # → 208 passed, 4 deselected
make test-security                # → 220 passed
.venv/bin/pytest -q               # → 2012 passed, 9 skipped, 8 deselected

```

If any of these diverge, stop and investigate before continuing.

### Step 1 — Decide: re-run final live-run or re-use `71ce478660bb`?

Two options, both defensible. **Recommendation: re-use
`71ce478660bb`** as the W20-5 final live-run evidence — that JSON
was captured AFTER the W20-1 + W20-2 flips were live in the
running container and already proves the acceptance bar. Running
another live container build (~5–15 min) on the same source state
adds no information.

**If you choose RE-USE (recommended):**

- Skip to Step 2.
- W20-5 self-stamp can cite `71ce478660bb` (sha256
  `cb402365a19474ad75bdd53925d5c89f947f541bd4554e7ee6d14463bd45cd83`)
  as the W20-end evidence.

**If you choose RE-RUN (defensive — overkill but valid):**

- STRICT pause point — announce before launching container build.
- Container is already up (last session brought it up); verify
  with `docker compose ps` — should show `automation_api`,
  `automation_executor`, `automation_db` all Up + healthy.
- If container is down: `docker compose up -d --build api executor`.
  Wait for both services healthy.
- Trigger analyze via curl (UI also works but curl is more
  reproducible). Run from repo root:

```bash
curl -s -X POST http://localhost:8000/api/marketplace/analyze/start \
  -H "Content-Type: application/json" \
  -d '{"publisher": "ms-python", "name": "python", "version": "2026.5.2026052501"}'
```

- Poll the job_id until `status: "completed"` (~7 min):

```bash
JOB_ID="<from above>"
for i in $(seq 1 60); do
  curl -s "http://localhost:8000/api/marketplace/analyze/$JOB_ID" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('status'), d.get('current_step', ''))"
  sleep 10
done
```

- Inspect the resulting `output/activation_report_*.json` (latest
  one in the dir) with the jq queries from Step 3 below.

### Step 2 — Land the close-out commit (preamble Active → Previous + tracker freeze + §18 self-stamp + cross-doc parity gate)

This is the W19-6 paterni mirror. Touches the same 9 canonical
docs as W20-0 doc-reconcile, plus the W20 tracker freeze + §18
final state in `REFACTOR_OPTIMIZATION.md`.

**Surface to update:**

- `documents/active-work/W20-coverage-promotion-easy-wins.md` —
  freeze the tracker:
  - `Phase:` line: `W20 closed synthetically 2026-05-26 — Hat-3
    easy-wins tier complete; W20-0..W20-4 closed (commit SHAs);
    W20-5 close-out this commit; PR week20 -> main PENDING USER
    APPROVAL`.
  - Add a final test bar block at the bottom of "Status (Quick
    Glance)" section.
  - W20-5 row in Sub-Iter Scope table: flip `planned → closed
    <date> via this commit` with the final live-run anchor JSON
    + sha256 cited.
  - Add a final "W20 Closure" section (mirroring W19's final
    self-stamp section) summarizing the 5/6 sub-iter audit trail
    and citing the live evidence.
- `documents/REFACTOR_OPTIMIZATION.md` §18:
  - Header flip: `W20-0 in-flight 2026-05-26 on the week20
    branch` → `W20 closed synthetically 2026-05-26; PR week20 ->
    main PENDING USER APPROVAL`.
  - W20-5 row flip `planned → closed`.
  - §18.4 Exit Criteria checklist: flip the `[x]` boxes for all
    closed items.
- `documents/POST_POC_BACKLOG.md` W20 Pull-Forward:
  - W20-5 row flip `planned → closed`.
  - Add a final acceptance summary block under the table
    (mirroring W19's at lines ~179-188).
- 9-doc canonical preamble across CLAUDE.md, README.md, AGENTS.md,
  documents/AGENT_CONTEXT.md, documents/active-work/README.md,
  documents/REFACTOR_STATUS.md, documents/REFACTOR_OPTIMIZATION.md,
  documents/POST_POC_BACKLOG.md,
  documents/active-work/W18-W22-roadmap.md:
  - Replace the `W20-0 doc-reconcile in-flight via this commit`
    prefix with a `W20 closed synthetically 2026-05-26 — W20-0..W20-5
    delivered; PR week20 -> main PENDING USER APPROVAL` prefix.
  - Update the `Active phase: W20` claim to keep matching the
    `test_doc_preamble_consistency.py` markers — the closed-but-not-merged
    lifecycle uses `W20 closed synthetically` form, which is
    accepted by both the doc-preamble-consistency regex pattern
    and the `test_readme_phase_pointer_tracks_active_w20_status`
    marker list.
- (Optional, recommended) New invariant test
  `tests/architecture/test_w20_section_18_cross_doc_parity.py`
  pinning the §18 self-stamp marker (sub-iter slate count +
  closed dates) across all canonical docs — mirrors the
  W19-6-followup-2 paterni that landed `test_canonical_preamble_parity.py`.
- README phase-pointer arch gate update:
  `tests/architecture/test_readme_phase_pointer.py` — no rename
  needed; the closed-synthetically marker is already in the
  accepted-marker list. (Only at W21-0 the file will get
  renamed to `_tracks_active_w21_status` and a new W20 close-out
  fact gate `test_readme_phase_pointer_mentions_w20_closeout_merge`
  pinning `PR #<W20 PR number>` / `week20 -> main` / `<merge SHA>`
  will be added.)

**Commit cadence — primary + self-stamp follow-up (W19-6 paterni):**

Primary commit message draft:

```text
chore(W20-5): close-out hygiene — preamble Active→Previous flip + §18 self-stamp + W20 tracker freeze + final live-run evidence

W20 (Coverage Promotion Round 1: Easy Wins) closes synthetically
2026-05-26 on the `week20` branch (per user direction; W11-W19
paterni preserved). 5 sub-iters delivered + 1 close-out: W20-0
doc-reconcile, W20-1 scm flip + 4 invariant tests, W20-2 settings
flip + 4 invariant tests, W20-3 coverage matrix contract invariants
(5 new tests), W20-4 comments+testing readiness DESIGN doc, W20-5
this commit. Total 10 commits prior + this close-out.

W20 acceptance bar (LIVE-SATISFIED via post-flip anchor
71ce478660bb):

- coverage_summary.missing_capabilities: 6 → 4 (dropped scm +
  settings) — must-pass
- coverage matrix contract tests green (13 invariant tests)
- W19 close-out holds post-W20: unaccounted_dropout == 0 +
  harness_verification_unconfirmed_present DROPPED

Close-out scope: 9-doc canonical preamble Active→Previous flip;
W20 tracker freeze per W17/W18/W19 paterni; §18 self-stamp; W20-5
row state flip; final live-run anchor pin.

Test bar at W20-5 close-out (unchanged from W20-4):

- tests/architecture/: 208 passed, 4 deselected
- make test-security: 220 passed
- full suite: 2012 passed, 9 skipped, 8 deselected

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>

```

### Step 3 — Final live-run jq inspection (re-use 71ce478660bb)

```bash
REPORT="output/activation_report_ms-python.python-2026.5.2026052501-71ce478660bb.json"
shasum -a 256 "$REPORT"
# Expect: cb402365a19474ad75bdd53925d5c89f947f541bd4554e7ee6d14463bd45cd83

# W19 Hat-1 (must-pass):
jq '[.event_attempts[] | select(.failure_reason_code == "unaccounted_dropout")] | length' "$REPORT"
# Expect: 0

# W19 Hat-2 (must-pass):
jq '.automation_health.reasons' "$REPORT"
# Expect: ["skipped_scenarios_present", "verification_gap_present", "official_unresolved_present"]
# (no "harness_verification_unconfirmed_present")

# W20 acceptance (must-pass):
jq '.coverage_summary.missing_capabilities' "$REPORT"
# Expect: ["chat", "comments", "testing", "workspace_trust"]
# (no "scm", no "settings"; 4 entries not 6)

# W20-1 scm flip live:
jq '.coverage_tracks.official.matrix[] | select(.capability == "scm") | .support_status' "$REPORT"
# Expect: "covered"

# W20-2 settings flip live:
jq '.coverage_tracks.official.matrix[] | select(.capability == "settings") | .support_status' "$REPORT"
# Expect: "covered"

```

If all five `jq` outputs match the expected values, the W20-5
close-out is safe to land.

### Step 4 — Push + PR (STRICT user "go" required)

**Do not run these without explicit user "go ahead" in the same
turn.** The memory entry `feedback_pr_push_approval.md` is strict:
"never push to remote or open/merge/close PRs without an explicit
user 'go ahead' in the same turn; plan-mode allowedPrompts ≠
standing authorization."

When user says "go":

```bash
git push -u origin week20

gh pr create --base main --head week20 --title "<PR title>" --body "$(cat <<'EOF'
## Summary

W20 — Coverage Promotion Round 1: Easy Wins. Closes the Hat-3
easy-wins tier (scm + settings official-track promotion) and
lifts broader coverage matrix contract invariants.

W20 sub-iter slate (W20-0..W20-5):

- W20-0: doc-reconcile — open week20 + §18 promote + 9-doc canonical
  preamble refresh + baseline live-run (`e89a82ca9ba8`).
- W20-1: `[GOAL taxonomy-scm-official-promotion]` —
  `_OFFICIAL_CAPABILITY_SUPPORT["scm"]: "missing" → "covered"` +
  4 invariant tests + fixture regen.
- W20-2: `[GOAL taxonomy-settings-official-promotion]` — mirror
  W20-1 for `settings`.
- W20-3: `[GOAL coverage-matrix-contract-tests]` — 5 broader
  invariant tests (keyset parity + Official ⊆ Heuristic + notes
  ↔ taxonomy + ordering + combined post-condition).
- W20-4: `[DESIGN taxonomy-comments-testing-readiness]` — W21
  plumbing şablonu (doc-only).
- W20-5: close-out hygiene + final live-run evidence + cross-doc
  parity gate.

Live acceptance evidence (`71ce478660bb`,
sha256 `cb402365...`):

- `coverage_summary.missing_capabilities`: 6 → 4 (dropped scm + settings) ✅
- `unaccounted_dropout` == 0 (W19 Hat-1 holds) ✅
- `harness_verification_unconfirmed_present` reason DROPPED (W19 Hat-2 holds) ✅
- `confirmation_source` distribution: harness_nonce=2 + log_record=6 + none=13 ✅

Final test bar:

- `tests/architecture/`: 208 passed, 4 deselected
- `make test-security`: 220 passed
- Full suite: 2012 passed, 9 skipped, 8 deselected (W19 baseline 1995 → +17)

## Test plan

- [ ] CI runs `tests/architecture/`, `make test-security`, and full
  suite to confirm the test bar holds in CI environment.
- [ ] Reviewer spot-checks `packages/analysis_planner/capabilities.py:88,90`
  for the two-character flip and the regenerated trigger payload
  fixture `tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json`.
- [ ] Reviewer reads `documents/architecture/comments-testing-readiness.md`
  for the W21 plumbing template.
- [ ] Reviewer confirms 9-doc canonical preamble parity (`tests/architecture/test_canonical_preamble_parity.py`).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"

```

After PR merges, run the post-merge audit (W19-post-merge-drift
paterni `93b2977`) to flip Active → Previous claims and update
`_EXPECTED_MERGE_FINGERPRINT` in
`tests/architecture/test_canonical_preamble_parity.py` from
`"PR #28"` / `"c879603"` to the new W20 PR number + merge SHA.

---

## STRICT Pause Points (DO NOT skip)

| Action | Approval |
|---|---|
| Local file edits + commits on `week20` | OK — free |
| Container rebuild + analyze re-run (Step 1 RE-RUN path) | **STRICT — announce + wait** |
| `git push -u origin week20` | **STRICT — explicit "go" in same turn** |
| `gh pr create --base main --head week20` | **STRICT — explicit "go" in same turn** |
| Post-merge audit commit on `main` | **STRICT — explicit "go" + only after PR merges** |

---

## Source-Of-Truth File Locations

### W20-specific

- **W20 active tracker**: `documents/active-work/W20-coverage-promotion-easy-wins.md`
- **W20 plan source**: `documents/REFACTOR_OPTIMIZATION.md` §18
- **W20 Pull-Forward Acceptance Bar**: `documents/POST_POC_BACKLOG.md` `## W20 Pull-Forward Acceptance Bar`
- **W21 readiness design doc** (W20-4 output): `documents/architecture/comments-testing-readiness.md`
- **Driving plan file (out-of-repo)**: `/Users/ekrem/.claude/plans/week20-i-in-yeni-bir-compressed-stallman.md`

### Source surface touched in W20

- **W20-1 flip**: `packages/analysis_planner/capabilities.py:88` (scm)
- **W20-2 flip**: `packages/analysis_planner/capabilities.py:90` (settings)
- **W20-1+W20-2+W20-3 invariants**: `tests/platform/contracts/test_capability_support_invariants.py` (13 tests)
- **Fixture regen**: `tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json`

### Doc-reconcile + arch gate surface

- `tests/architecture/test_readme_phase_pointer.py` — `_w20_status` + new W19 close-out fact gate
- `tests/architecture/test_canonical_preamble_parity.py` — `_CANONICAL_PREAMBLE_DOCS` tuple swapped W19→W20 tracker

### Live evidence

- `output/activation_report_ms-python.python-2026.5.2026052501-e89a82ca9ba8.json` (W20-0 baseline, pre-flips)
- `output/activation_report_ms-python.python-2026.5.2026052501-71ce478660bb.json` (W20-1+W20-2 post-acceptance — **W20-5 final candidate**)
- `output/activation_report_ms-python.python-2026.5.2026052001-992ad028f3df.json` (W19 baseline reference)

### Multi-iter roadmap

- `documents/active-work/W18-W22-roadmap.md`
- `documents/active-work/W19-live-run-root-cause.md` (frozen at W19-6-followup-2)
- `documents/active-work/W18-heartbeat-refactor.md` (frozen at W18-4)

### Test gate references

- `tests/platform/contracts/test_capability_support_invariants.py` (W20)
- `tests/platform/contracts/test_coverage_model.py` (existing — Pydantic CoverageSummary)
- `tests/workflows/marketplace/test_analysis_planner.py` (frozen fixture round-trip)
- `tests/architecture/test_doc_preamble_consistency.py` (`Active phase: W<N>` regex gate)
- `tests/architecture/test_canonical_preamble_parity.py` (merge fingerprint pin)
- `tests/architecture/test_readme_phase_pointer.py` (close-out fact gates)

---

## Open Questions For The User

1. **W20-0 spec crosswalk research scope.** The W20 plan
   ([W18-W22-roadmap.md](W18-W22-roadmap.md) §W20) listed a
   `[RESEARCH activation-event-spec-crosswalk]` item under
   W20-0 — three-source crosswalk (resmi VS Code Activation
   Events sayfası ↔ repo OFFICIAL_EVENT_REGISTRY 29 entry ↔
   DB `ExtensionActivationEvents` + downloaded VSIX
   `package.json` `activationEvents[]`). The W20-4 design doc
   (`documents/architecture/comments-testing-readiness.md`)
   covers comments + testing but NOT the full three-source
   crosswalk. Two clean choices for W20-5:
   - (a) Treat the W20-4 doc as broader than crosswalk and
     mark `[RESEARCH activation-event-spec-crosswalk]` as
     `deferred to W22-6 if W22-6 reveals gap`. (Recommended —
     the live runs already show no missing activation event
     trigger surface; crosswalk research is best done when
     it can drive action.)
   - (b) Pull the crosswalk into W20-5 close-out scope (~2
     hours additional work: read the VS Code spec page, dump
     the DB + manifest entries, produce the matrix). Risks
     W20-5 close-out scope explosion.
2. **W20-5 final live-run: re-use vs re-run.** See Step 1 above.
   Recommendation: re-use `71ce478660bb`.
3. **Post-merge `_EXPECTED_MERGE_FINGERPRINT` bump.** After
   the W20 PR merges, the `test_canonical_preamble_parity.py`
   fingerprint should bump from `"PR #28"` / `"c879603"` to the
   new W20 PR number + merge SHA. This is a post-merge audit
   commit (W19-post-merge-drift paterni `93b2977`) — typically
   direct on `main`, no PR. Confirm this is your intended
   close-out flow before pushing.
4. **W19 frozen tracker preamble.** The W19 tracker (frozen at
   W19-6-followup-2 per W17/W18 paterni) still says "live smoke
   pending" in its banner. The W20-0 baseline live-run on
   `e89a82ca9ba8` retired that marker. Two choices:
   - (a) Leave W19 tracker frozen as-is (consistent with
     W17/W18 frozen-tracker paterni — never edit frozen).
   - (b) Land a small `docs(W19-post-merge-live-verified)`
     commit on `main` (direct or via PR) that adds a "live
     smoke confirmed via W20-0 baseline" note to the W19
     tracker's banner. Could ship alongside or after the W20
     close-out. Probably overkill — the W20-0 self-stamp
     commit (`5f13757`) already carries the live evidence in
     its own preamble.

---

## Commands The Next Session Will Need

### Verify state

```bash
git rev-parse --abbrev-ref HEAD                   # → week20
git log --oneline main..week20 | wc -l            # → 10
git status                                         # → clean

```

### Re-run static test bar

```bash
.venv/bin/pytest tests/architecture/ -q            # → 208 passed
make test-security                                  # → 220 passed
.venv/bin/pytest -q                                 # → 2012 passed

```

### Inspect W20 acceptance live (re-use evidence)

```bash
REPORT="output/activation_report_ms-python.python-2026.5.2026052501-71ce478660bb.json"
shasum -a 256 "$REPORT"
jq '.coverage_summary.missing_capabilities' "$REPORT"
jq '.coverage_tracks.official.matrix[] | select(.capability == "scm" or .capability == "settings") | {capability, support_status, status}' "$REPORT"
jq '[.event_attempts[] | select(.failure_reason_code == "unaccounted_dropout")] | length' "$REPORT"
jq '.automation_health.reasons' "$REPORT"

```

### Optional re-run live (only on explicit user "go")

```bash
docker compose ps                                  # confirm containers up
# If down: docker compose up -d --build api executor; wait for healthy

curl -s -X POST http://localhost:8000/api/marketplace/analyze/start \
  -H "Content-Type: application/json" \
  -d '{"publisher":"ms-python","name":"python","version":"2026.5.2026052501"}'

# Poll job_id with /api/marketplace/analyze/$JOB_ID until status=completed (~7 min)

```

### Push + PR (only on explicit user "go")

```bash
git push -u origin week20
gh pr create --base main --head week20 --title "..." --body "..."

```

---

## Memory-Style Notes (Project Facts The Next Session May Not Derive)

- **Branch lifetime**: `week20` is cut from `main @ 52a47f4` — the
  W19 close-out post-merge cross-doc parity gate commit. Every
  W20 commit is on `week20`. **Nothing was pushed to origin**;
  there's no `origin/week20`.
- **Container state**: The Docker stack is up (last started by
  the previous session for the W20-0 baseline live-run).
  `docker compose ps` will show `automation_api`,
  `automation_executor`, `automation_db` as Up + healthy.
- **W19-X handoff doc** at `documents/active-work/W19-X-handoff.md`
  is the structural template this doc follows (W19 paterni was
  about debugging; this one is about close-out execution).
- **Pre-commit hooks**: All commits in W20 went through ruff +
  mypy + markdownlint + Markdown Link Check successfully. The
  W20 commit work touched markdownlint's MD056 (table column
  count) once during W20-0; the fix was to remove the
  intermediate `"planned"` cell and merge with the next column
  (so each row has 4 cells matching the W19 paterni header).
  If you regenerate any sub-iter table, mind the column count.
- **AskUserQuestion answers in the previous session**:
  - "Baseline live-run timing": W20-0 baseline + W20-5 final (user chose).
  - "Container hardening pull": Hayır, W21-4'te kalsın (user chose).
  - "Live-run launch path": "Ben başlatayım — docker compose
    up -d --build + jq inspection" (user pre-approved live-run
    execution path).
- **The W19 tracker is `documents/active-work/W19-live-run-root-cause.md`**;
  the W20 tracker is `documents/active-work/W20-coverage-promotion-easy-wins.md`.
  The frozen W19 tracker is NOT in the
  `_CANONICAL_PREAMBLE_DOCS` parity-gate tuple anymore (W20-0
  swap); the W20 tracker IS.
- **The `Active phase: W20` regex marker** is required for the
  doc-preamble-consistency gate. The W20-0 banner edit chose
  this exact phrase. When flipping to closed-synthetically at
  W20-5, the new accepted form is `W20 closed synthetically`
  (or `W20 fully closed synthetically`) — both are in the
  `_ACTIVE_PHASE_PATTERNS` regex set.
- **The `harness_verification_unconfirmed_present` reason was
  expected to drop only synthetically**, but the W20-0 baseline
  live-run captured `e89a82ca9ba8` confirmed the synthetic
  close-out IS live-verified — meaning W19 Hat-2 is fully
  closed live, not just synthetically. This is significant
  evidence the user may want to surface explicitly.

---

## Open Items NOT For W20-5

Per the W20 Pull-Forward Acceptance Bar
([POST_POC_BACKLOG.md](../POST_POC_BACKLOG.md)), these
forward-refs are tracked but explicitly out of W20 scope:

- `[RESEARCH activation-event-spec-crosswalk]` — W22-6 implement
  if gap surfaces (see Open Question #1 above for the W20-5
  decision).
- `[FOLLOWUP harness-secret-extra-reactivation-source]` (W19-X
  migrated) — opportunistic W20-5 ONLY if the final live-run
  diagnostic surfaces `poll_attempts > 1`. **The W20-0 baseline
  did NOT surface this** (`harness_nonce` count = 2 means both
  reactivation paths got the secret), so this stays deferred
  unless re-confirmed at re-run.
- `[FOLLOWUP harness-secret-distribution-redesign]` — W20-W22
  ADR candidate; not for W20-5.
- `[FOLLOWUP defensive-test-parametrize-helper]` (W19-3-followup-2
  audit) — not for W20-5.

---

## What "Done" Looks Like For This Handoff

The new session has finished W20-5 close-out when:

- [ ] State verification (Step 0) passed.
- [ ] W20-5 close-out commit (Step 2 primary) landed.
- [ ] Optional `test_w20_section_18_cross_doc_parity.py` arch
  gate landed (W19-6 paterni).
- [ ] W20-5 self-stamp follow-up landed (mirrors W19-6-followup-2:
  preamble drift fix if needed + tracker freeze stamp).
- [ ] User explicitly said "go" → `git push -u origin week20`
  succeeded.
- [ ] User explicitly said "go" → `gh pr create` succeeded.
- [ ] PR URL captured and returned to user.
- [ ] (Post-merge, separate turn) Post-merge audit commit on
  `main` flipping Active → Previous + bumping
  `_EXPECTED_MERGE_FINGERPRINT` for the next phase opening.

At that point W20 is fully closed and W21-0 doc-reconcile can
open (next session, separate handoff).
