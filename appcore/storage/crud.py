"""Public CRUD facade for ExTrace storage."""

from appcore.storage.crud_ops.analysis_jobs import (
    JobNotCancellableError,
    cancel_analysis_job,
    complete_analysis_job,
    create_analysis_job,
    fail_analysis_job,
    get_active_analysis_job,
    get_analysis_job,
    recover_interrupted_analysis_jobs,
    update_analysis_job,
    update_analysis_job_step,
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
    "JobNotCancellableError",
    "cancel_analysis_job",
    "complete_analysis_job",
    "create_analysis_job",
    "create_extension",
    "delete_extension",
    "fail_analysis_job",
    "get_active_analysis_job",
    "get_analysis_job",
    "get_db_extensions_base_info",
    "get_extension_activation_events",
    "get_extension_by_id",
    "get_extension_capabilities",
    "get_extension_contributes_all",
    "get_extension_contributes_commands",
    "get_extension_scripts",
    "get_extensions_all_info",
    "get_operator_setting",
    "list_operator_settings",
    "recover_interrupted_analysis_jobs",
    "search_extension_by_name",
    "update_analysis_job",
    "update_analysis_job_step",
    "upsert_operator_setting",
    "upsert_operator_settings_bulk",
    "upsert_operator_settings_bulk_and_commit",
]
