# Archive

`Last Updated: 2026-04-29`

This folder is **frozen reference**. Coding agents do **not** read it on the
default path. Open a file under `archive/` only when:

- the user explicitly asks for historical detail, or
- a slim canonical doc points to a specific archive file with
  "details: archive/...".

## Layout

- `plans/`
  - frozen full snapshots of `documents/REFACTOR_OPTIMIZATION.md`
- `status/`
  - frozen full snapshots of `documents/REFACTOR_STATUS.md`
- `backlog/`
  - frozen full snapshots of `documents/POST_POC_BACKLOG.md`
- `reviews/`
  - point-in-time external review reports
    (`claude_code_review.md`, `codex_project_review.md`)

Slim canonical doc is at the original path under `documents/`. Archive
filenames are dated (`*_full_<YYYY-MM-DD>.md`) so multiple snapshots can
coexist without collision.

## Rule For Future Drops

When a canonical doc grows past its budget (see
`documents/agent-lanes/docs-maintenance.md` invariants), drop a dated full
snapshot here, then trim the canonical. Do not rewrite or curate archive
files — they are point-in-time records.
