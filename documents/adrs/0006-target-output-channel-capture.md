# ADR 0006: Target Output-Channel Capture

- Status: Accepted
- Date: 2026-04-27
- Amended: 2026-04-27 — §5 wording softened: PR5 establishes the
  evidence surface and wires it into ``EventAttemptRecord`` lifecycle
  reconciliation, but the full ``target_extension_observed``
  conjunction tightening is filed as a follow-up so baseline fixtures
  can stabilize first.
- Related: ADR 0002 (Threat Model §4 Trust Boundaries), ADR 0003
  (Detection Taxonomy §4 Attribution, §5 Verdict Rollup), ADR 0005
  (Packages Charter)

## Context

ExTrace's evidence chain currently captures four target-attributed
signal classes: filesystem events (strace + inotify), network events
(tshark), process events (strace process tree), and exthost.log
activation lifecycle markers (PR345 PR1-3). One first-class behavioral
signal that target extensions emit is **missing**: writes to
`vscode.window.createOutputChannel` channels (and to a lesser extent
plain `console.log` calls) made from inside the target extension.

A grep across `executor/flows/playwright/runtime_capture/` confirms zero
coverage today for `OutputChannel.appendLine` or
`channel.append` invocations. The mechanical effects show up indirectly
in `extension_host.py` log scraping, but the channel name, the per-line
boundary, and the timestamp of each `appendLine` are reconstructed at
best heuristically and at worst not at all (multiple writes within the
same exthost log flush coalesce).

Reference points:

- [`executor/flows/harness_extension/extension.js:11-128`](../../executor/flows/harness_extension/extension.js)
  — harness `activate()` already emits structured `[extrace-harness]`
  markers via `console.log`; the channel is well-known and
  attribution-side filters can ignore it.
- [`executor/flows/harness_extension/markers.js:15-22`](../../executor/flows/harness_extension/markers.js)
  — `emitHarnessMarker(phase, details)` is the existing marker shape;
  PR2 of PR345 already exercises this channel as the
  `event_attempts` correlation source.
- [`packages/analysis_contracts/contracts.py::EvidenceEvent`](../../packages/analysis_contracts/contracts.py)
  — current `kind` value space is filesystem/network/process/activation;
  no terminal output-channel kind.
- [`executor/flows/playwright/attribution/events.py:62-80`](../../executor/flows/playwright/attribution/events.py)
  — `_actor_from_*` filters route events to `extension`/`unknown` based
  on `is_target_extension_event`; no harness-collector exclusion exists
  today because no harness-emitted EvidenceEvent exists today.

The W7 demo report and the post-fail-fast `sim-all` review both flagged
this as a known evidence-chain gap: a target extension that writes its
exfiltration breadcrumbs into an Output channel produces less detection
signal than the same extension writing them to a file. Detection rules
that consume `target_extension_observed` already overrate cases where
activation fired but no target-owned signal followed (the conjunction
fix in PR5 closes this).

## Decision

Capture target-owned output-channel writes (and, for downstream
extension by the same mechanism, `console.log` calls inside the target
extension) by hooking `vscode.window.createOutputChannel` from the
harness extension and emitting each `append`/`appendLine` invocation
as an `EvidenceEvent` with a new `kind` value
(`output_channel_appendline`). This is **Option (a)** below; Option
(b) is documented as the fallback path.

### 1. Two options considered

| Axis | (a) Harness-side hook | (b) exthost log bundle parse |
|---|---|---|
| Signal fidelity | Per-line, per-channel, per-timestamp | Coarse; channel name reconstructed from log heuristics; `appendLine` boundaries lost when a line wraps or coalesces |
| Implementation cost | Small JS Proxy + 1 new EvidenceEvent kind + 1 attribution filter line | New parser module + heuristics for VS Code log Output panel format |
| Harness-coupling risk | Harness becomes a co-actor; attribution filter must exclude `collector="harness_extension"` | None |
| Cross-extension contamination | Hook captures **every** extension's channels, including non-target VS Code core extensions; must filter by attribution at emit time or at evidence-builder time | None |
| Future portability | Stable across VS Code 1.116+; depends on `vscode.window.createOutputChannel` API stability (decade-old, no deprecation signal) | Fragile across VS Code versions; log format has changed multiple times |
| Parse cost | Sub-millisecond per line | Bounded by exthost.log size |
| Detection rule sharpness | High — full text + channel name = direct match against secret-read or beacon-format patterns | Low — partial text + ambiguous channel attribution |

**Option (a) is the recommended baseline**. Option (b) is documented as
a fallback path: if PR5 review surfaces an attribution leakage that the
collector-exclusion filter cannot cleanly close, this ADR is amended
(not replaced) and (b) becomes the live path. The amendment route keeps
the decision history visible.

### 2. Harness-side hook contract

The harness installs the hook in its `activate()` function, before any
non-harness extension activates:

```javascript
const _origCreate = vscode.window.createOutputChannel;
vscode.window.createOutputChannel = (name, ...rest) => {
    const ch = _origCreate.call(vscode.window, name, ...rest);
    const wrap = (fn) => (...args) => {
        emitHarnessMarker({
            kind: "output_channel_appendline",
            channel: name,
            text: String(args[0] ?? ""),
            ts: Date.now(),
            collector: "harness_extension"
        });
        return fn.apply(ch, args);
    };
    ch.append = wrap(ch.append);
    ch.appendLine = wrap(ch.appendLine);
    return ch;
};
```

The hook installs **once** per Extension Host process; subsequent
extensions calling `createOutputChannel` see the wrapped factory.
`emitHarnessMarker` already serializes a single-line JSON payload to
`console.log` with the `[extrace-harness]` prefix the existing PR2
exthost-log scrape consumes; this ADR reuses that channel rather than
introducing a second IPC route.

### 3. EvidenceEvent kind extension

`EvidenceEvent.kind` gets a new allowed value:
`output_channel_appendline`. Adjacent to the existing five
(`http_request`, `http_response`, `dns_query`, `tls_client_hello`,
`tcp_connect`). The Pydantic mirror in
`packages/analysis_contracts/contracts.py` adds the same value; the UI
contract regen picks it up via the existing
`scripts/generate_ui_contracts.py` flow.

`raw_context` carries `{"channel": "<name>", "text": "<truncated_line>",
"collector": "harness_extension"}`. Text is truncated to the existing
500-char `EvidenceEvent` payload preview limit so output-channel
floods cannot bloat the report.

### 4. Attribution filter (harness exclusion)

`executor/flows/playwright/attribution/events.py` `_actor_from_*` gain a
short-circuit:

```python
if event.collector == "harness_extension":
    return "harness"
```

Harness-emitted events stay observable in the evidence chain
(detection rules can still read `kind="output_channel_appendline"`)
but they do not get attributed to the target extension's identity.
Detection rules that gate on `is_target_extension_event=True` ignore
them; rules that read all output-channel events see them all.

When the wrapped `appendLine` fires from a non-target extension's
output channel, the resulting EvidenceEvent's `actor` is determined by
the **calling extension's** attribution at the exthost-log scrape
boundary, not by the harness `collector` field. The harness collector
is a marker of who *emitted* the EvidenceEvent, not who *triggered*
the underlying API call.

### 5. Lifecycle and `target_extension_observed` consequences

PR5 contributes evidence in two places:

- **Lifecycle reconciliation (landed with PR5).**
  ``health_reconciliation._target_log_stream_summaries`` excludes
  ``kind == "activation"`` log entries (the activation entry alone is
  not a separate post-activation signal) and harvests
  ``ActivationReport.output_signal_events`` whose
  ``is_target_extension_event=True`` as a second evidence source.
  Result: an ``EventAttemptRecord`` upgrades from
  ``activation_seen`` to ``target_log_seen`` when, **on top of** a
  matching activation entry, the report carries either a non-activation
  target-owned log entry or a target-attributed output-channel event.

- **`target_extension_observed` (full conjunction tightening
  deferred).** The eventual conjunction form is:

  ```text
  target_extension_observed = (
      has_event_attempt_status_at_least("activation_seen")
      AND (
          has_target_owned_log_entry
          OR has_target_owned_output_signal_event
      )
  )
  ```

  As of 2026-04-27, ``ActivationReport.target_extension_observed``
  carries an **additive OR** clause for target-attributed output
  signals (alongside the legacy activation/running/file/network
  predicates). The full conjunction ``activation_seen AND
  (log OR output_signal)`` is deferred so baseline fixtures
  (``ms-python.python``, the chat/theme benign baselines, and the
  T1 canaries) can be re-validated against the stricter rule without
  forcing a flag-day churn. The follow-up is tracked in
  ``POST_POC_BACKLOG.md`` as the "ADR 0006 §5 conjunction tightening"
  entry; ``REFACTOR_STATUS.md`` PR345 closure section also flags it.

This staging removes the false-positive class where an extension
activated during the monitoring window but never emitted any
target-owned runtime signal — but does so in two steps: PR5
upgrades the lifecycle status, and the follow-up upgrades the
top-level observation predicate.

### 6. Dockerfile harness checksum re-generation

The harness file change in PR5 means
[`executor/container/Dockerfile:117-123`](../../executor/container/Dockerfile)
re-runs the existing
`find /home/executor/flows/harness_extension -type f -print0 | xargs -0
sha256sum > /home/executor/flows/harness_extension.sha256` step on
rebuild. No additional Dockerfile change required; the existing
checksum manifest naturally picks up the new hook.

## Consequences

### Positive

- Per-line, per-channel, per-timestamp output-channel signal feeds the
  evidence chain.
- `target_extension_observed` becomes a meaningful conjunction rather
  than an activation-presence proxy.
- Detection rules that match exfiltration breadcrumbs in Output
  channels (today: zero coverage) become writeable in the existing
  rule framework.
- Harness already proves the marker channel works; the hook is a
  small additive PR rather than a new capture pipeline.

### Negative

- Harness becomes a co-actor that can emit EvidenceEvents; the
  `collector="harness_extension"` filter is now load-bearing in
  attribution.
- Hook captures **every** extension's output channels, not just the
  target's. Filtering happens at attribution time; a bug in the
  filter could leak harness-collected text into target-attributed
  evidence.
- Output-channel floods (verbose logging from popular extensions like
  Pylance) increase per-run report size; the 500-char text truncation
  - the existing per-event evidence cap bound the worst case.
- Wrapping `vscode.window.createOutputChannel` is a runtime monkey-patch
  on a VS Code core API. If a future VS Code version replaces the
  factory with a frozen reference, the hook silently stops firing —
  the regression is observable only by the absence of new EvidenceEvent
  records, not by an explicit error. (Mitigated in step 1 follow-on
  below.)

### Follow-On

- **PR5** implements (a) per the contract in §2-§5; PR5 cannot land
  before this ADR.
- A short smoke test in `tests/executor/test_harness_extension_hooks.py`
  (added with PR5) asserts that calling
  `vscode.window.createOutputChannel("test").appendLine("x")` from a
  spawned harness session results in an EvidenceEvent with
  `kind="output_channel_appendline"` and `collector="harness_extension"`.
  The test runs against the bundled VS Code in the executor container,
  not a mock — a silent hook regression on a VS Code upgrade trips it.
- If PR5 review surfaces attribution leakage that the
  `collector="harness_extension"` filter cannot cleanly close, this ADR
  is amended (not replaced); the amendment elevates Option (b) to the
  live path and downgrades Option (a) to a documented alternative.
- ADR 0002 §4 trust-boundary table will pick up an entry for the
  harness extension as a "co-actor inside the sandbox" in the same
  change set as PR5; ADR 0002 itself stays the authoritative threat
  model.
- POST_POC_BACKLOG.md "Next iteration" `target_extension_observed`
  tightening item is closed by PR5 once this ADR lands; the entry
  moves to the LANDED log alongside PR5.
