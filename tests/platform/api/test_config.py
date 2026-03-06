from __future__ import annotations

from appcore.api.config import DatabaseSettings


def test_database_url_prefers_database_url_env(monkeypatch) -> None:
    override_url = "postgresql://override-user:override-pass@db.example.com:5432/app"
    monkeypatch.setenv("DATABASE_URL", override_url)

    settings = DatabaseSettings()

    assert settings.url == override_url
