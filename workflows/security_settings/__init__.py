"""Operator-facing security settings (currently VSIX hardening thresholds).

Backed by the ``operator_settings`` key-value table; service layer in
``service.py`` adds default-fallback so the analysis pipeline always
gets a complete threshold dict even when the table is empty (fresh
install / migration regression).
"""

from workflows.security_settings.defaults import (
    THRESHOLD_BOUNDS,
    VSIX_THRESHOLD_DEFAULTS,
    VSIX_THRESHOLD_KEYS,
    VsixThresholdBounds,
)
from workflows.security_settings.service import (
    SecuritySettingValidationError,
    load_vsix_thresholds,
    save_vsix_thresholds,
)

__all__ = [
    "THRESHOLD_BOUNDS",
    "VSIX_THRESHOLD_DEFAULTS",
    "VSIX_THRESHOLD_KEYS",
    "SecuritySettingValidationError",
    "VsixThresholdBounds",
    "load_vsix_thresholds",
    "save_vsix_thresholds",
]
