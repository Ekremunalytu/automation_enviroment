from __future__ import annotations

import pytest
from pydantic import ValidationError

from appcore.api.config import DatabaseSettings, StaticAnalysisSettings


def test_database_url_prefers_database_url_env(monkeypatch) -> None:
    override_url = "postgresql://override-user:override-pass@db.example.com:5432/app"
    monkeypatch.setenv("DATABASE_URL", override_url)

    settings = DatabaseSettings()

    assert settings.url == override_url


def test_static_analysis_timeout_budget_defaults_to_ten_minutes(monkeypatch) -> None:
    monkeypatch.delenv("STATIC_ANALYSIS_TIMEOUT_BUDGET_S", raising=False)

    settings = StaticAnalysisSettings(_env_file=None)

    assert settings.TIMEOUT_BUDGET_S == 600


@pytest.mark.parametrize("budget", [4, 601])
def test_static_analysis_timeout_budget_rejects_out_of_bounds_values(
    budget: int,
) -> None:
    with pytest.raises(ValidationError):
        StaticAnalysisSettings(_env_file=None, TIMEOUT_BUDGET_S=budget)
