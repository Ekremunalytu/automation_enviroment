"""Pin the W12-2 attribution_summary key rename + population semantics.

`build_attribution_summary` produces two non-target counters that operators
historically confused because the names overlapped (``background_activation_count``
vs ``competing_candidate_count``). W12-2 renamed them to
``target_background_activation_count`` (target extension's non-foreground
activations only) and ``competing_extension_event_count`` (file/network events
attributed to *other* extensions in the target's activation window). This test
verifies the populations stay disjoint and the key names match the W12-2
contract.

Closes ``[FOLLOWUP w12-attribution-naming-overlap]``.
"""

from __future__ import annotations

from types import SimpleNamespace

from executor.flows.playwright.annotation import build_attribution_summary


def _is_background_activation(activation_event: str) -> bool:
    return activation_event in {"onStartup", "onStartupFinished"}


def _count_target_activations(activated: list, target_extension_id: str) -> int:
    return sum(1 for entry in activated if entry.extension_id == target_extension_id)


def test_target_background_and_competing_extension_counts_disjoint() -> None:
    target_id = "publisher.target"

    report = SimpleNamespace(
        target_extension_id=target_id,
        activated=[
            SimpleNamespace(
                extension_id=target_id,
                activation_event="onStartupFinished",
            ),
            SimpleNamespace(
                extension_id=target_id,
                activation_event="onCommand",
            ),
            SimpleNamespace(
                extension_id="publisher.other",
                activation_event="onStartupFinished",
            ),
        ],
        file_events=[
            SimpleNamespace(attribution_status="competing_candidate"),
            SimpleNamespace(attribution_status="competing_candidate"),
            SimpleNamespace(attribution_status="target_attributed"),
        ],
        network_events=[
            SimpleNamespace(attribution_status="competing_candidate"),
            SimpleNamespace(attribution_status="near_target_activation"),
        ],
        target_file_events=[],
        target_network_events=[],
        ui_blocker_entries=[],
    )

    summary = build_attribution_summary(
        report,
        count_target_activations=_count_target_activations,
        is_background_activation=_is_background_activation,
    )

    # The two counters describe disjoint populations (target activations vs
    # non-target events) and must not share a value.
    assert summary["target_background_activation_count"] == 1
    assert summary["competing_extension_event_count"] == 3
    # ``correlated_only_event_count`` includes both competing + near-target.
    assert summary["correlated_only_event_count"] == 4


def test_attribution_summary_keys_match_w12_2_contract() -> None:
    report = SimpleNamespace(
        target_extension_id="publisher.target",
        activated=[],
        file_events=[],
        network_events=[],
        target_file_events=[],
        target_network_events=[],
        ui_blocker_entries=[],
    )

    summary = build_attribution_summary(
        report,
        count_target_activations=_count_target_activations,
        is_background_activation=_is_background_activation,
    )

    # The pre-W12-2 keys ``background_activation_count`` and
    # ``competing_candidate_count`` must be gone; the W12-2 replacements
    # must be present. UI adapter (``ui/src/lib/adapters/report.ts``) and the
    # contract typings (``ui/src/lib/types/contracts.ts``) read these names.
    assert "background_activation_count" not in summary
    assert "competing_candidate_count" not in summary
    assert "target_background_activation_count" in summary
    assert "competing_extension_event_count" in summary
