# packages/analysis_engine

`Last Updated: 2026-07-31`

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
- Trusted-domain matching is shared through
  `packages.analysis_contracts.trusted_entities`; the reviewed JSON catalog is
  also consumed by the Rules API/UI so detection behavior and operator-visible
  ownership cannot drift.

This package stays framework-agnostic per ADR 0005: no imports from
`appcore/`, `workflows/`, `executor/`, or `ui/`.
