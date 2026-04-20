"""Detection rule namespace."""

from packages.analysis_engine.rules.base import DetectionRule
from packages.analysis_engine.rules.registry import (
    get_all_rules,
    get_production_rules,
    register,
)

__all__ = ["DetectionRule", "get_all_rules", "get_production_rules", "register"]
