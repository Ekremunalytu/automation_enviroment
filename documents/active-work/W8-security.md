# W8 — Security Hardening (Past Work Tracker)

`Last Updated: 2026-05-07 (slimmed; W8 closed)`

Canonical past-work tracker for W8 stable IDs (`W8-1` … `W8-9`). Code,
tests, ADR addenda, and backlog items may reference these IDs, so keep them
stable. Full W8 detail is archived at:

- [`archive/status/W8-security_full_2026-05-07.md`](../archive/status/W8-security_full_2026-05-07.md)
- [`archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md`](../archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md)

## Status

- **W8-1 — landed `2026-04-27`.** VSIX zip-bomb and entry-count guards:
  `MAX_UNCOMPRESSED_SIZE`, `MAX_COMPRESSION_RATIO`, `MAX_FILE_COUNT`,
  `VSIXUnpackError`, and `test_vsix_hardening.py`.
- **W8-2 — landed `2026-04-27`.** Safe marketplace identity helper:
  `packages/marketplace_identity/safe_marketplace_slug`.
- **W8-3 — landed `2026-04-28`.** URI trigger argv-form invocation and
  shell-template regression guard.
- **W8-4 — landed `2026-04-29`.** Absolute binary paths via
  `executor/binary_paths.py`; remaining known pragmas are tracked by
  `[FOLLOWUP w8-4-broader-executor]`.
- **W8-5 — landed `2026-04-29`.** Activation-report router slug regex
  consolidation through shared validators and AST drift gate.
- **W8-6 — landed `2026-04-29`.** `ContentSample` Pydantic carrier and
  `redact_secrets` taxonomy. Later follow-ups cover consumers outside
  the original carrier path.
- **W8-7 — landed `2026-04-29`.** ADR 0007 local-network-binding
  defaults: loopback binds by default, LAN opt-in via `EXTRACE_ALLOW_LAN`,
  CDP debug profile, and `test_default_bindings.py`.
- **W8-8 — deferred `2026-04-29`, not abandoned.** Manifest field
  log-injection sanitization reopens on the first real manifest-field log
  emit site or an explicit proactive security gate. Stable follow-up:
  `[FOLLOWUP w8-8-manifest-emit-when-needed]`.
- **W8-9 — landed `2026-05-02`.** External-review follow-up: workspace
  fixture path containment and HTTP body-preview redaction.

## Deferred Trigger For W8-8

W8-8 ships only when one of these triggers fires:

- **Trigger A:** a production logger call starts emitting attacker-controlled
  manifest fields such as `displayName`, `description`, `repository.url`,
  `categories[]`, `homepage`, `bugs`, `qna`, or `license`.
- **Trigger B:** an external review or stakeholder gate explicitly asks for
  the defense-in-depth helper before a real emit site exists.

When either trigger fires, land the sanitizer helper, platform security test,
AST gate, and ADR 0002 addendum in the same PR. Then mark
`[FOLLOWUP w8-8-manifest-emit-when-needed]` landed in `POST_POC_BACKLOG.md`.

## Exit Record

- W8 is closed for active work as of `2026-04-29`.
- `make test-security` includes the W8 security lanes that landed during
  W8; W8-8-specific tests are deferred with W8-8.
- ADR 0007 is Accepted and implemented.
- ADR 0008 container packaging was picked up by W9 and is now Accepted.
