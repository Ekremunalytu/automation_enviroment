# packages/analysis_engine

`Last Updated: 2026-04-23`

This package owns trusted analysis logic that must stay outside sandbox-local
executor modules so that detection rules can run against any
`ActivationReport` source.

Current surfaces (W5 landed `2026-04-20`, W6 correctness follow-up
`2026-04-23`):

- `runner.py`
  - executes registered rules against an `ActivationReport`, propagating
    `RuleExecutionStatus` (ADR 0003 error dominance honored upstream by the
    automation-health rollup)
- `rules/`
  - PoC Must-class detection rules: `a1_credential_read_then_network`,
    `a2_startup_network_beacon`, `a4_workspace_exfil`, `a6_ui_spoof`. Rules
    consume only `ActivationReport` data and gate on target-only attribution
    via `target_file_events` /
    `target_unknown_outbound_network_events`.
- `rules/registry.py`
  - rule registration entry points and discovery helpers
- `allowlists/`
  - allowlist data files (e.g. `benign_domains.txt`) consumed by rules

This package stays framework-agnostic per ADR 0005: no imports from
`appcore/`, `workflows/`, `executor/`, or `ui/`.
