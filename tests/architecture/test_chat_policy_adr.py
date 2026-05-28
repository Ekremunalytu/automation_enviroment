"""W22-1 chat policy ADR existence + content invariants (ADR 0014).

Pins the policy decision recorded in
`documents/adrs/0014-chat-and-language-model-tool-policy.md` so the
W22-2 chat coverage promotion (`[GOAL taxonomy-chat-coverage]`)
inherits a stable, machine-checkable source of truth for its
implementation shape.

What's pinned:

1. The ADR 0014 file exists at the expected path so a future edit
   that removes or relocates it trips this gate before W22-2
   downstream invariants regress.
2. The ADR 0014 body carries the Option C decision markers
   (registration API names, the no-external-services boundary, the
   stable-API engine compatibility claim, and the W22-2 unblock
   reference) so the document cannot be silently rewritten to a
   different posture without breaking this test alongside the
   downstream W22-2 invariants in
   `tests/platform/contracts/test_capability_support_invariants.py`.

What's intentionally NOT pinned here:

- The W22-2 runtime implementation details (extension.js + scenarios
  + capabilities.py flips) are pinned in the
  capability-support-invariants module that lands with W22-2 itself.
- Engine-version specifics beyond the "stable surfaces only" claim
  — those live with `executor/flows/harness_extension/package.json`.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ADR_PATH = (
    REPO_ROOT / "documents" / "adrs" / "0014-chat-and-language-model-tool-policy.md"
)


def test_adr_0014_exists() -> None:
    """ADR 0014 file must remain at the expected path so the
    W22-2 chat coverage promotion has a documented source-of-truth
    for the local-only, stable-API-only policy decision.
    """
    assert ADR_PATH.exists(), (
        f"ADR 0014 not found at {ADR_PATH.relative_to(REPO_ROOT)}. "
        "W22-2 [GOAL taxonomy-chat-coverage] depends on the policy "
        "decision recorded here — restore the ADR before re-running."
    )


def test_adr_0014_documents_option_c_decision() -> None:
    """ADR 0014 must explicitly carry the Option C decision markers
    (registration API names, no-external-services boundary, stable-
    API engine claim, W22-2 unblock reference) so a future rewrite
    that quietly flips the posture surfaces here alongside the
    downstream capability-support invariants.
    """
    text = ADR_PATH.read_text(encoding="utf-8")
    required_tokens = (
        "Option C",
        "vscode.chat.createChatParticipant",
        "vscode.lm.registerTool",
        "vscode.lm.invokeTool",
        "must not call external services",
        "engines.vscode",
        "1.90",
        "W22-2",
    )
    missing = [token for token in required_tokens if token not in text]
    assert not missing, (
        "ADR 0014 must carry the Option C decision markers so the "
        "W22-2 chat coverage implementation inherits an unambiguous "
        f"policy contract. Missing tokens: {missing!r}."
    )
