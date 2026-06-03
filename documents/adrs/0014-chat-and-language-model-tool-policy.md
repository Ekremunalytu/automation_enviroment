# ADR 0014 — Chat Participant + Language Model Tool Policy

- Status: Accepted (`2026-05-28`)
- Date: 2026-05-28
- Authors: ekrem + Claude
- Driving phase: W22-1 — `[GOAL taxonomy-chat-policy-adr]` — unblocks
  W22-2 `[GOAL taxonomy-chat-coverage]` (chat hard-tier promotion
  closing `missing_capabilities` 1 → 0)

## Context

The marketplace analyzer's coverage taxonomy
(`packages/analysis_planner/capabilities.py`) tracks per-capability
support across two parallel tracks (`_OFFICIAL_CAPABILITY_SUPPORT`,
`_GLOBAL_CAPABILITY_SUPPORT`). After W21-2 promoted `comments` to
`covered`, the sole remaining `missing` capability is `chat`. The
W21-4 baseline live-run anchor (`eacea0b6690e`) confirmed
`coverage_summary.missing_capabilities = ["chat"]` (1 item). W22-2
closes the hard tier by promoting `chat` to `covered`.

`chat` is the **hard tier** because it spans two distinct VS Code
API surfaces:

1. **`vscode.chat.createChatParticipant(id, handler)`** — registers a
   chat participant that fires `onChatParticipant:<id>` activation
   events when the user invokes `@id`. Pure local API; no model
   round-trip required for *registration*.
2. **`vscode.lm.*`** — language-model tool surface
   (`vscode.lm.registerTool`, `vscode.lm.invokeTool`, plus the
   chat-model APIs `vscode.lm.selectChatModels` / `sendRequest`)
   firing `onLanguageModelTool:<name>` activation events. Tool
   registration + invocation is local; *chat-model interaction* is
   provider-bound (Copilot, third-party providers, etc.).

The pre-W22-1 policy seed at `capabilities.py:63-66` already
declared the boundary:

> "Chat participant and language-model tool coverage remain
> local-only and must not call external services."

`AGENTS.md` reinforces the same rule project-wide: the marketplace
analyzer must never depend on an external model provider, network
egress, or non-deterministic LLM responses for activation-event
coverage. The open W22-1 question was *how* to satisfy this
constraint while still firing the relevant activation events.

The harness today (`executor/flows/harness_extension/`) does NOT
register a chat participant or a language model tool. The existing
`stimulus_dispatch.js:52-60` placeholder only types `@<value>
harness` into the chat input box — UI navigation only, no
API-level activation event reliably fires, no harness marker emits.
That placeholder must be replaced.

## Decision

**Adopt Option C — tool-only coverage with an explicit local boundary.**

The harness covers `chat` activation-event families exclusively via
**locally-registered**, **stable**, **network-free** VS Code APIs:

1. **`vscode.chat.createChatParticipant("extrace.harness.chat",
   noopChatHandler)`** at `activate()` — fires
   `onChatParticipant:extrace.harness.chat` and any
   `onChatParticipant:*` wildcard activation. The handler returns
   immediately without invoking any chat model.
2. **`vscode.lm.registerTool("extrace-harness-lm-tool",
   { invoke: noopToolInvoke })`** at `activate()` — fires
   `onLanguageModelTool:extrace-harness-lm-tool` and any
   `onLanguageModelTool:*` wildcard activation. `noopToolInvoke`
   returns `new vscode.LanguageModelToolResult([new
   vscode.LanguageModelTextPart("extrace-harness-noop")])` — a
   synthesized response with no model call.
3. **`vscode.lm.invokeTool("extrace-harness-lm-tool", { input:
   { stimulus: value } })`** invoked from `stimulus_dispatch.js`
   under the `onLanguageModelTool` family branch — exercises the
   tool invocation path end-to-end and emits a marker.

All three surfaces are **GA since VS Code 1.90.0** (`vscode.chat`
and `vscode.lm.registerTool`/`invokeTool` are part of the stable
extension API as of mid-2024). The existing
`executor/flows/harness_extension/package.json` `engines.vscode:
"^1.90.0"` already covers them; **no engine bump, no
`enabledApiProposals` entry, no Insiders build is required.**

> Naming constraint (post-implementation correction): both surfaces
> must be declared under `contributes` in `package.json`, otherwise VS
> Code rejects the runtime registration (`chatParticipant must be
> declared in package.json` / `Tool "<name>" was not contributed`). The
> language-model **tool name is validated against `/^[\w-]+$/`** (dots
> are invalid), so the tool id is `extrace-harness-lm-tool` — a
> dot-free identifier — rather than the dotted `extrace.harness.*`
> convention used elsewhere. The chat participant **`name`** (the
> `@`-handle) is likewise `/^[\w-]+$/`-validated, so it is `harness`,
> while its **`id`** keeps the dotted `extrace.harness.chat`. Parity
> between the `extension.js` registrations and the `package.json`
> contributions is pinned by
> `tests/architecture/test_harness_extension_manifest_parity.py`.

### API Surface Boundary

| Activation event | Covered by | Marker kind | Invocation site |
|---|---|---|---|
| `onChatParticipant:*` | `vscode.chat.createChatParticipant` at `activate()` | `chat_participant_state` (phase=`registered` at activate, phase=`stimulated` per stimulus dispatch, phase=`disposed` at deactivate) | `extension.js#activate` + `stimulus_dispatch.js#onChatParticipant` branch |
| `onLanguageModelTool:*` | `vscode.lm.registerTool` at `activate()` + `vscode.lm.invokeTool` from stimulus dispatch | `lm_tool_state` (phase=`registered` at activate, phase=`invoked` per stimulus dispatch, phase=`disposed` at deactivate) | `extension.js#activate` + `stimulus_dispatch.js#onLanguageModelTool` branch |

**Out of scope (explicit boundary):**

- No `vscode.lm.selectChatModels()` calls — that surface requires a
  provider (Copilot or similar) and would make a network round-trip.
- No `vscode.lm.registerChatModelProvider()` — proposed API, not GA.
- No third-party chat model providers, no Anthropic/OpenAI/Copilot
  SDK linkage.
- No invocation of an actual chat handler beyond a `return;`
  no-op; participants are exercised at the *registration* surface,
  not at the *response* surface.

### Security Posture

The chat participant's handler body is a synchronous no-op
(`return;`). The language-model tool's `invoke` returns a canned
`LanguageModelToolResult` constructed in-process from a fixed
string (`"extrace-harness-noop"`). Neither path executes
attacker-controlled code, opens a network connection, persists
state across activations, or interacts with any external service.

Marker emit follows the W19-X Bug B paterni: every state transition
is signed via `emitHarnessEvent` and routes through the reserved
`"ExTrace Harness"` OutputChannel (HMAC-signed marker contract,
W13-1 secret distribution). This keeps chat markers indistinguishable
from the comments/testing/workspace_trust markers downstream
parsers already trust.

### W19-X Lesson Application

W19-X close-out surfaced three live-run failure modes with
analogous marker surfaces:

- **Bug B** (marker channel destination — markers routed to
  `console.log` were lost; reserved OutputChannel is the only
  trusted route). W22-2 chat + LM markers MUST use
  `emitHarnessEvent` → reserved OutputChannel. No console-only
  variants.
- **Bug C** (HMAC reactivation race — persistent state across
  stimulus passes caused signed-marker drift). W22-2 chat
  participant + LM tool subscriptions live on
  `context.subscriptions`, disposed automatically on extension
  deactivation. Stimulus dispatch path uses `invokeTool` as a
  one-shot call, no retained state.

### Engine Compatibility

- `vscode.chat.createChatParticipant`: GA in VS Code 1.90 (June
  2024).
- `vscode.lm.registerTool` / `vscode.lm.invokeTool`: GA in VS Code
  1.90 (June 2024).
- `vscode.LanguageModelToolResult` + `vscode.LanguageModelTextPart`:
  GA in VS Code 1.90.
- `executor/flows/harness_extension/package.json` `engines.vscode:
  "^1.90.0"` — **no bump required**. **No
  `enabledApiProposals` entry required.** **No Insiders build
  required.**

## Consequences

### Positive

- Unblocks W22-2 `[GOAL taxonomy-chat-coverage]` — chat hard tier
  closure. After W22-2 lands, `coverage_summary.missing_capabilities`
  is expected to drop from `[chat]` → `[]` (W22 must-pass acceptance
  #6).
- Closes the open design question at `capabilities.py:63-66` policy
  seed (W20-4) with an Accepted ADR — the harness implementation
  shape is no longer ambiguous.
- Establishes a reusable pattern: future activation-event surfaces
  that *look* network-bound can be covered via local registration
  + no-op invocation when a stable, local API exists.
- The covered surface is byte-identical in shape to W21-2 comments
  (`CommentController`-style registration + ephemeral lifecycle),
  so the harness extension keeps a coherent style.

### Negative

- Coverage is at the *registration + invocation surface*, not at
  the *model response surface*. A misbehaving extension that hides
  its activation behind a real chat-model interaction (i.e.,
  triggers only after a `sendRequest` round-trip) would not be
  exercised. This matches the AGENTS.md no-external-services rule
  and is the documented limit, not a defect.
- The harness gains a permanent dependency on the chat + LM tool
  API surfaces. A future VS Code breaking change to either would
  require harness updates. Mitigation: the `engines.vscode`
  constraint is the explicit pin; breaking changes would force a
  conscious engine-version review.

### Operational notes

W22-2's implementation lands the runtime code (extension.js +
stimulus_dispatch.js diffs), the taxonomy flips
(`capabilities.py`), the scenario entries
(`scenarios.py:local_chat_participant_controller` +
`local_language_model_tool_controller`), and the invariant tests
(`tests/platform/contracts/test_capability_support_invariants.py`
+5). The runtime live-run smoke (`make sim-target
TARGET=ms-python.python`) at W22-2 self-stamp is the acceptance
gate — anchor must show
`coverage_summary.missing_capabilities == []`.

## Status / next steps

- W22-1 commit lands this ADR + the existence test
  (`tests/architecture/test_chat_policy_adr.py`).
- W22-2 commit lands the runtime implementation per the API
  Surface Boundary table above.
- Future iterations may explore covering the *chat model
  interaction* surface via a local stub model provider once
  `vscode.lm.registerChatModelProvider` reaches GA — out of scope
  for W22.

## Alternatives Rejected

**Option A — Stub model provider via
`vscode.lm.registerChatModelProvider`.** Would let the harness
register a fake chat model and exercise the full request/response
loop. **Rejected** because `registerChatModelProvider` is a
proposed API (mid-2026) requiring `enabledApiProposals` in
`package.json` and an Insiders build of VS Code for stability.
Adopting it would force an engine constraint bump + a proposed-API
opt-in, both contrary to the "stable surfaces only" project stance
established by W13-W21 close-outs.

**Option B — Mock `invokeTool` without registration.** Calls
`vscode.lm.invokeTool` against a tool ID that the harness has not
registered. **Rejected** because `invokeTool` against an
unregistered ID throws synchronously; we would either need to
register the tool first (collapsing into Option C) or wrap the
call in a try/catch that silently swallows the failure. Either way
the registration step is unavoidable, and adding a try/catch only
hides the activation-event semantics.

**Option D — Declare `chat` permanently `partial` with a documented
blocker.** Leave the official + heuristic tracks at `partial` and
list "no local LM provider" as the reason. **Rejected** because
the activation events (`onChatParticipant:*` and
`onLanguageModelTool:*`) are both fully exercisable via stable
local API. Declaring `partial` would create a permanent backlog
item without an actual blocker and would leave `missing_capabilities`
non-empty indefinitely. Option C closes the hard tier cleanly.

## References

- `documents/adrs/0002-threat-model.md` — A1–A7 adversary classes
  (Option C's security posture aligns with A5 "extension calls
  external service" — the harness never does, so it does not
  introduce that surface).
- `documents/adrs/0010-extrace-executor-logger-consolidation.md` —
  reserved OutputChannel route (`"ExTrace Harness"`) used by the
  marker contract.
- `documents/adrs/0013-container-isolation-baseline.md` —
  containment baseline that bounds the blast radius if a future
  harness change accidentally adds a network call.
- `packages/analysis_planner/capabilities.py:63-66` — pre-existing
  policy seed for chat (W20-4) that this ADR now formalizes.
- VS Code Extension API — `vscode.chat` namespace and `vscode.lm`
  namespace (stable since 1.90.0). Reference:
  `https://code.visualstudio.com/api/references/vscode-api`.
- W19-X close-out — harness marker channel destination Bug B and
  HMAC reactivation race Bug C, both lessons applied here.
