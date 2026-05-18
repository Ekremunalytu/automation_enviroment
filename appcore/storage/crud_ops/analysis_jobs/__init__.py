"""Read/write helpers for persisted marketplace analysis jobs.

Thin re-export facade for the W11-8 subpackage split. Callers continue to
import from ``appcore.storage.crud_ops.analysis_jobs`` (or, more commonly,
through ``appcore.storage.crud``); the lifecycle/steps split is invisible
to the import path. Logic lives in the focused modules — this file is
gated by ``test_analysis_jobs_facade_stays_thin`` against re-growth.
"""

from .lifecycle import (
    JobNotCancellableError as JobNotCancellableError,
)
from .lifecycle import (
    WorkerEntryClaim as WorkerEntryClaim,
)
from .lifecycle import (
    WorkerEntryOutcome as WorkerEntryOutcome,
)
from .lifecycle import (
    cancel_analysis_job as cancel_analysis_job,
)
from .lifecycle import (
    claim_queued_analysis_job_at_worker_entry as claim_queued_analysis_job_at_worker_entry,  # noqa: E501
)
from .lifecycle import (
    complete_analysis_job as complete_analysis_job,
)
from .lifecycle import (
    create_analysis_job as create_analysis_job,
)
from .lifecycle import (
    fail_analysis_job as fail_analysis_job,
)
from .lifecycle import (
    finalize_cancelled_analysis_job as finalize_cancelled_analysis_job,
)
from .lifecycle import (
    get_active_analysis_job as get_active_analysis_job,
)
from .lifecycle import (
    get_analysis_job as get_analysis_job,
)
from .lifecycle import (
    recover_interrupted_analysis_jobs as recover_interrupted_analysis_jobs,
)
from .lifecycle import (
    update_analysis_job as update_analysis_job,
)
from .steps import (
    update_analysis_job_step as update_analysis_job_step,
)

__all__ = [
    "JobNotCancellableError",
    "WorkerEntryClaim",
    "WorkerEntryOutcome",
    "cancel_analysis_job",
    "claim_queued_analysis_job_at_worker_entry",
    "complete_analysis_job",
    "create_analysis_job",
    "fail_analysis_job",
    "finalize_cancelled_analysis_job",
    "get_active_analysis_job",
    "get_analysis_job",
    "recover_interrupted_analysis_jobs",
    "update_analysis_job",
    "update_analysis_job_step",
]
