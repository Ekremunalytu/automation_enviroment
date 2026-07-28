"""Public CRUD facade for ExTrace storage."""

from appcore.storage.crud_ops.analysis_jobs import (
    STALE_HEARTBEAT_REAP_ERROR_CODE,
    JobNotCancellableError,
    cancel_analysis_job,
    complete_analysis_job,
    create_analysis_job,
    fail_analysis_job,
    finalize_cancelled_analysis_job,
    get_active_analysis_job,
    get_analysis_job,
    reap_stale_running_analysis_jobs,
    recover_interrupted_analysis_jobs,
    reject_analysis_job_static,
    touch_analysis_job_heartbeat,
    update_analysis_job,
    update_analysis_job_step,
)
from appcore.storage.crud_ops.blacklist_domains import (
    add_blacklist_domain_and_commit,
    list_blacklist_domains,
    remove_blacklist_domain_and_commit,
)
from appcore.storage.crud_ops.operator_settings import (
    get_operator_setting,
    list_operator_settings,
    upsert_operator_setting,
    upsert_operator_settings_bulk,
    upsert_operator_settings_bulk_and_commit,
)
from appcore.storage.crud_ops.reads import (
    get_db_extensions_base_info,
    get_extension_by_id,
    get_extension_inventory_summary,
    get_extensions_all_info,
    search_extension_by_name,
)
from appcore.storage.crud_ops.relations import (
    get_extension_activation_events,
    get_extension_capabilities,
    get_extension_contributes_all,
    get_extension_contributes_commands,
    get_extension_scripts,
)
from appcore.storage.crud_ops.writes import create_extension, delete_extension

__all__ = [
    "STALE_HEARTBEAT_REAP_ERROR_CODE",
    "JobNotCancellableError",
    "add_blacklist_domain_and_commit",
    "cancel_analysis_job",
    "complete_analysis_job",
    "create_analysis_job",
    "create_extension",
    "delete_extension",
    "fail_analysis_job",
    "finalize_cancelled_analysis_job",
    "get_active_analysis_job",
    "get_analysis_job",
    "get_db_extensions_base_info",
    "get_extension_activation_events",
    "get_extension_by_id",
    "get_extension_capabilities",
    "get_extension_contributes_all",
    "get_extension_contributes_commands",
    "get_extension_inventory_summary",
    "get_extension_scripts",
    "get_extensions_all_info",
    "get_operator_setting",
    "list_blacklist_domains",
    "list_operator_settings",
    "reap_stale_running_analysis_jobs",
    "recover_interrupted_analysis_jobs",
    "reject_analysis_job_static",
    "remove_blacklist_domain_and_commit",
    "search_extension_by_name",
    "touch_analysis_job_heartbeat",
    "update_analysis_job",
    "update_analysis_job_step",
    "upsert_operator_setting",
    "upsert_operator_settings_bulk",
    "upsert_operator_settings_bulk_and_commit",
]
