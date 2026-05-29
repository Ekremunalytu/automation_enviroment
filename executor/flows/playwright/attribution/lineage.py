"""pid-lineage attribution for file-capture child-process ownership.

Split from ``attribution/events.py`` (LOC-hotspot ratchet): the two helpers
here turn the strace-observed owning PID on each ``FileEvent`` into causal
ownership. ``build_target_pid_lineage`` derives the set of PIDs the target
extension spawned (and their descendants); ``classify_pid_lineage_upgrade``
applies that set to an individual file event. ``annotate_file_events`` calls
the latter as a fallback that only ever upgrades — never downgrading a
tight-window temporal match and never touching inotify telemetry.
"""

from __future__ import annotations

from ..runtime_capture.events import ProcessEvent

_PID_LINEAGE_CONFIDENCE = 0.80
_PID_LINEAGE_BASIS = (
    "owning process descends from a child the target extension "
    "spawned during activation (pid lineage)"
)


def build_target_pid_lineage(
    process_events: list[ProcessEvent],
    target_extension_id: str,
) -> set[int]:
    """PIDs causally owned by the target extension via spawn lineage.

    Seeds from ``spawn`` events already attributed to the target (children the
    target spawned inside its activation window, per
    :func:`annotate_process_events`), then closes over descendants: any process
    whose parent is owned is owned too. The shared extension-host root PID is
    never a spawn child within the trace, so it is excluded by construction.

    Consumed by ``annotate_file_events`` to attribute child-process file I/O to
    the target even when the I/O timestamp falls outside the temporal window.
    Iterating in chronological order guarantees a parent is classified before
    its child, so a single pass closes the lineage.
    """
    if not target_extension_id:
        return set()
    owned: set[int] = set()
    for event in sorted(
        process_events,
        key=lambda entry: (
            entry.rel_time_s is None,
            entry.rel_time_s if entry.rel_time_s is not None else 0.0,
            entry.pid,
        ),
    ):
        if event.operation != "spawn":
            continue
        if event.is_target_extension_event or (
            event.ppid is not None and event.ppid in owned
        ):
            owned.add(event.pid)
    return owned


def classify_pid_lineage_upgrade(
    *,
    observer: str,
    pid: int | None,
    is_target_extension_event: bool,
    target_extension_id: str,
    lineage_pids: set[int],
) -> tuple[str, str, float, str, bool, str] | None:
    """Upgrade a strace file event whose owning PID is target-owned.

    Returns the replacement
    ``(status, basis, confidence, related_extension_id, is_target, noise)``
    tuple when the event's PID descends from a process the target spawned
    during its activation, else ``None``. Never fires for inotify, for events
    already attributed to the target, or for unowned PIDs — so it only ever
    upgrades, never downgrading a tight-window temporal match.
    """
    if (
        observer != "strace"
        or is_target_extension_event
        or not target_extension_id
        or pid is None
        or pid not in lineage_pids
    ):
        return None
    return (
        "target_attributed",
        _PID_LINEAGE_BASIS,
        _PID_LINEAGE_CONFIDENCE,
        target_extension_id,
        True,
        "",
    )
