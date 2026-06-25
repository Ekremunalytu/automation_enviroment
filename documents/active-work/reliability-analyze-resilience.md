# Reliability — Analyze Resilience (multi-analyze + self-defense)

`Last Updated: 2026-06-25`

`Status: landed directly on main (reliability fixes, not a named-stream PR). B2 committed 4437d1e (2026-06-24); A + B committed 2026-06-25. Live-verified on the running stack (api + executor rebuilt).`

Direct-to-main reliability hardening that emerged from two concrete failures on
the running appliance. Not a weekly phase and not a named-stream PR — small,
verified fixes recorded here so the audit trail and the corrected root-causes are
not lost. Connects to the v1.0 bar **B1** (un-hangable by its own input), **B2**
(survives back-to-back use), and **B3** (never silently wedges).

## B2 — same-container multi-analyze reset (`reset_state.py`) — committed `4437d1e`

Closes `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` and
`[BUG reset-cdp-needle-stale]`.

**Corrected root cause (the backlog diagnosis was incomplete).** The backlog
attributed the 2nd-analyze `reset_sandbox` rc=1 to "the needle keys on a CDP flag
the default boot no longer sets" (a CDP-off problem). Live diagnosis proved the
real defect is more fundamental and bites in **every** config:
`terminate_vscode()` ran `pgrep -f --remote-debugging-port` **without a `--`
separator**, so pgrep parsed the `--`-prefixed pattern as an unknown option and
exited 2 → `_find_vscode_pids()` returned `[]` → terminate **silently no-op'd
even with CDP ON** (verified live: `reset_state` printed `vscode_terminated=0`
while the main `code` PID carried `--remote-debugging-port=9222`). The stale VS
Code instance + its orphaned integrated-terminal shells (separate `setsid`
sessions) survived every reset and accumulated across analyses.

**Fix (3 layers):**

1. `pgrep -f -- <needle>` — the `--` separator (the proven blocker).
2. CDP-independent needle `--extensionDevelopmentPath` (main-process-only; present
   in every config incl. the CDP-off Podman/air-gapped deploy).
3. Reap the whole descendant tree via a subprocess-free `/proc` PPID walk
   (`_read_proc_table` + `_process_tree`) so the orphan-prone terminal shells are
   killed, not left to accumulate. (No new bare-binary pragma → pragma ratchet
   untouched.)

**Tests:** `tests/executor/test_reset_state.py` — pgrep `--` guard, CDP
independence, `/proc` parse with comment-containing comm, full-tree signal.
Live-verified: new needle finds the main PID; the tree walk reaps the main + the
two bash terminals.

## B — analyze timeout left a CPU-bound zombie (`host.py`) — committed `2026-06-25`

`[BUG analyze-timeout-no-incontainer-kill]`.

**Incident.** A `GitHub.copilot-chat` analyze blew the 1800s `_AUTOMATION_TIMEOUT`.
The host-side `subprocess.run(timeout=…)` killed the `docker exec` **client**, but
the in-container entrypoint kept running — observed `~35 min`, `State R`, ~100%
CPU, no open files, no syscalls (pure compute in report-build), then it finally
finalized a complete report and exited.

**Root cause.** `entrypoint/__main__.py` installs a SIGTERM handler (W22) that
converts the first SIGTERM into a SystemExit graceful unwind; that SystemExit is
only raised between bytecode ops, so a CPU-bound C-stage ignores it. The W22
design relies on a **second** SIGTERM (handler resets to `SIG_DFL`) to hard-kill,
but `_cleanup_stale_entrypoint_processes()` sent only **one** `pkill` SIGTERM —
the zombie burned CPU and held the single-active sandbox past its deadline,
wedging the next analyze.

**Fix.** `_cleanup_stale_entrypoint_processes()` now escalates **SIGTERM →
grace (10s) → SIGKILL**; when no entrypoint is running (the common
reset-before-next-analyze case) the first `pkill` matches nothing and it returns
immediately (no grace delay). `host.py` is baked into `automation_api`, so it
deploys via `docker compose build api`.

**Tests:** `tests/executor/test_host_entrypoint_cleanup.py` — escalation when
running, no-escalation/no-delay when idle, ExecutorError swallowed. Live-verified:
the re-run copilot analyze completed in **160s with no zombie**.

## A — adaptive early-give-up for non-responsive targets (`stimulus/passes.py`) — committed `2026-06-25`

`[GOAL stimulus-early-giveup-nonresponsive-target]`.

**Why.** copilot-chat declared ~558 command/activation targets; the layered plan
attempted each (`558 event_attempt` + ~554 effect-waits ≈ 28 min) but copilot
cannot auth/network in the sandbox, so **no attempt produced any effect** — the
interaction phase alone exceeded the 1800s budget.

**Fix.** `run_stimulus_plan` tracks a **cheap, in-memory** target reaction signal
(`target_file_events + target_network_events`; deliberately NOT
`capture_runtime_snapshot`, whose renderer round-trip + log reparse a prior
per-attempt early-exit proved too slow). After `_NO_REACTION_GIVEUP_ATTEMPTS`
(60) consecutive attempts with no growth, it stops and marks the remaining plan
skipped via the generalized `_abort_remaining_attempts` (reason
`skipped_after_early_giveup`) + a `stimulus_early_giveup` automation event. Any
single real reaction resets the counter, so a responsive extension runs the full
plan. Threshold is generous → low coverage-loss risk (the operator accepted the
trade-off 2026-06-25).

**Tests:** `tests/executor/test_stimulus_early_giveup.py` — gives up when the
target never reacts, runs the full plan when it does, records the give-up event,
cheap-counter helper edge cases. + 153 stimulus/dispatch/accountant regression
tests green. Deployed-executor proof: a 65-attempt plan → give-up after 60 (5
skipped with `skipped_after_early_giveup`).

## Incidental (not fixed here)

In the verification re-run, copilot-chat **did not activate** (only built-in
`vscode.*` extensions appeared in `activated`), so build_triggers produced a
minimal 1-attempt plan and the verdict was honestly `inconclusive / needs_review`
("target not observed"). Likely a missing base-`GitHub.copilot` dependency or a
sign-in gate — an **analysis-fidelity** question, separate from these reliability
fixes. Left as an open observation.
