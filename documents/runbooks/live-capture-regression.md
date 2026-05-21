# Runbook: Live Capture Regression

`Last Updated: 2026-04-24`

## Symptom

Offline detection tests stay green but live-capture tests break:

- `make test-security` → **passed** (offline; uses hand-built fixture
  reports).
- `make test-security-live` → **failed** (real executor + real tshark).
- A4 TLS rules (and related A2/A6 rules that depend on outbound TLS
  evidence) report zero matches even though the target clearly made
  outbound HTTPS calls.
- `ActivationReport.evidence_events` contains network events but none with
  `event_type = "tls_client_hello"` (or a regression re-introduced the old
  vocabulary where only `tls_sni` existed).

This is the **most fragile detection path** in the project. A regression
here is silent under `make test-security` because that lane uses mock
fixtures —
only `test-security-live` exercises the tshark-to-rule wiring.

## Immediate Triage

```bash
# 1. What does make test-security-live actually require?
grep -A4 '^test-security-live:' Makefile

# 2. Did the live run even produce a report?
ls -lt output/activation_report_*.json | head -3

# 3. Are there TLS events in the latest live report?
jq '[.evidence_events[] | select(.event_type | test("^tls"))] | group_by(.event_type) | map({type: .[0].event_type, count: length})' \
   output/activation_report_*.json | head -20
```

If step 3 shows only `tls_sni` and no `tls_client_hello`, the vocabulary
regression has recurred — see Root-Cause Classes below.

## Diagnose

**TLS event vocabulary** (source: [packages/analysis_engine/rules/_common.py:16](../../packages/analysis_engine/rules/_common.py)):

```python
TLS_EVENT_TYPES: frozenset[str] = frozenset({"tls_sni", "tls_client_hello"})
```

Both types **must** stay in this set. The W6 correctness follow-up on
`2026-04-23` specifically added `tls_client_hello` after discovering that
live tshark captures emit that event type but the rules were only looking
for legacy `tls_sni`. Offline fixtures happened to use `tls_sni`, so the
test-security lane missed the gap.

**Where the event type is decided** (source: [executor/flows/playwright/runtime_capture/network.py](../../executor/flows/playwright/runtime_capture/network.py)):

The network-event builder reads tshark fields and sets `event_type` based
on which fields are present. A `tls_client_hello` is emitted when an SNI
field exists but the HTTP/DNS fields do not. If the tshark output format
changes or the builder's conditional changes, the event type silently
shifts to `unknown` or gets dropped entirely.

**Verify tshark itself still produces ClientHello frames:**

```bash
# Inside the executor container, run a short live capture
docker exec automation_executor bash -c '
  timeout 10 tshark -i any -f "tcp port 443" \
    -e frame.time_epoch \
    -e tls.handshake.type \
    -e tls.handshake.extensions_server_name \
    -E separator="|" 2>/dev/null | head -20
'
```

You should see lines where `tls.handshake.type = 1` (ClientHello) and the
SNI field is populated. If the ClientHello frames are missing entirely,
tshark or the libpcap permissions are broken, not the ExTrace rules.

**Cross-check offline test coverage for the vocabulary:**

```bash
grep -rn 'tls_client_hello' tests/security/ packages/analysis_engine/ \
  executor/flows/playwright/runtime_capture/
```

There should be offline test cases in `tests/security/rules/` that assert
A2/A4 rules accept `tls_client_hello` (search for the function name
`test_a2_accepts_live_tls_client_hello_vocabulary` or similar). If none
exist anymore, the regression guard is gone and needs to be restored.

## Recover

> A live-capture regression is almost always a **code fix**, not an
> operational recovery. This runbook is about triaging whether the
> problem is capture, rules, or wiring.

**Step 1 — Localize the failure:**

- If tshark produces ClientHello frames but the report has no
  `tls_client_hello` events → bug in
  [runtime_capture/network.py](../../executor/flows/playwright/runtime_capture/network.py)
  (builder stopped emitting the type).
- If the report has `tls_client_hello` events but A4 TLS rules still
  report zero matches → bug in the rule or in `TLS_EVENT_TYPES`
  ([rules/_common.py](../../packages/analysis_engine/rules/_common.py)).
- If tshark itself produces nothing → capture-side issue: permissions
  (`CAP_NET_RAW`), docker-compose capability settings, or an interface
  mismatch.

**Step 2 — Write an offline regression test first (before fixing code):**

Any fix for this class of bug should come with a fixture-based test under
`tests/security/rules/` that parses a report containing a
`tls_client_hello` event and asserts the rule matches. Without that test,
the regression will recur because `make test-security` cannot catch it
today — the test runs the entire live path, which CI does not exercise.

**Step 3 — Rerun the live lane locally:**

```bash
make test-security-live
```

This is marked break-glass in the Makefile (requires explicit opt-in).

## Root-Cause Classes

- **Vocabulary drift.** Someone renamed or removed `tls_client_hello` from
  `TLS_EVENT_TYPES` without updating live-path tests. The 2026-04-23 fix
  added this, but nothing prevents a future commit from removing it again
  if the CI security-fixtures lane does not explicitly assert it.
- **Tshark field changes.** Upstream tshark releases occasionally change
  field names (e.g. `tls.handshake.extensions_server_name` → something
  else). The network-event builder must use the specific fields emitted
  by the tshark version in the executor image.
- **Builder condition order.** The event-type selector in
  `runtime_capture/network.py` checks fields in order. If a later check
  shadows the `tls_client_hello` branch, TLS events silently downgrade to
  `unknown`.
- **Capture dropped by the kernel.** If tshark fell behind under load, the
  ClientHello packet may never have been captured. Look for "Packets
  dropped" counts in the tshark stderr.

## Code References

- [packages/analysis_engine/rules/_common.py](../../packages/analysis_engine/rules/_common.py)
  — `TLS_EVENT_TYPES`, `network_events`, `outbound_network_events`
- [packages/analysis_engine/rules/](../../packages/analysis_engine/rules/)
  — A2 (`a2_*`), A4 (`a4_*`) rule families that consume TLS events
- [executor/flows/playwright/runtime_capture/network.py](../../executor/flows/playwright/runtime_capture/network.py)
  — tshark field parsing and `event_type` assignment
- [tests/security/](../../tests/security/) — offline rule tests; live tests
  are gated on the `test-security-live` Make target
- [Makefile](../../Makefile) — `test-security`, `test-security-live` target
  definitions (grep `test-security`)
- [documents/adrs/0003-detection-taxonomy.md](../adrs/0003-detection-taxonomy.md)
  — detection vocabulary, severity/confidence, rule lifecycle
- [documents/adrs/0004-malicious-fixture-policy.md](../adrs/0004-malicious-fixture-policy.md)
  — fixture tiering (T1 in CI, T3 break-glass only)
