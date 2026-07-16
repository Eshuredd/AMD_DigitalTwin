from __future__ import annotations

import configparser
import os
from pathlib import Path
import subprocess

from app.persistence.config import (
    DEFAULT_DATABASE_URL,
    get_persistence_settings,
    persistence_startup_summary,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SUPERVISOR_CONF = REPO_ROOT / "docker" / "supervisord.conf"
DOCKERFILE = REPO_ROOT / "Dockerfile"
ALEMBIC_ENV = REPO_ROOT / "backend" / "alembic" / "env.py"
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"


def _supervisor_config() -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(SUPERVISOR_CONF)
    return parser


def test_backend_supervisor_does_not_override_database_environment() -> None:
    backend = _supervisor_config()["program:backend"]
    environment = backend.get("environment", "")

    assert "CROPTWIN_DATABASE_URL" not in environment
    assert "CROPTWIN_STATE_STORE" not in environment
    assert "CROPTWIN_AUTO_CREATE_DB" not in environment


def test_supervisor_public_and_internal_ports_are_correct() -> None:
    config = _supervisor_config()
    backend_command = config["program:backend"]["command"]
    frontend_command = config["program:frontend"]["command"]

    assert "uvicorn app.main:app" in backend_command
    assert "--host 127.0.0.1" in backend_command
    assert "--port 8000" in backend_command
    assert "--host 0.0.0.0" not in backend_command

    assert frontend_command.startswith('/bin/sh -c "exec streamlit run')
    assert "--server.address 0.0.0.0" in frontend_command
    assert "--server.port ${PORT:-7860}" in frontend_command
    assert "--server.headless true" in frontend_command


def test_streamlit_shell_port_expression_expands_runtime_port() -> None:
    base_env = {
        key: value
        for key, value in os.environ.items()
        if key != "PORT"
    }

    fallback = subprocess.run(
        ["/bin/sh", "-c", 'printf "%s" "${PORT:-7860}"'],
        check=True,
        capture_output=True,
        text=True,
        env=base_env,
    )
    override = subprocess.run(
        ["/bin/sh", "-c", 'printf "%s" "${PORT:-7860}"'],
        check=True,
        capture_output=True,
        text=True,
        env={**base_env, "PORT": "10000"},
    )

    assert fallback.stdout == "7860"
    assert override.stdout == "10000"


def test_docker_healthcheck_uses_public_streamlit_runtime_port() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")

    assert "HEALTHCHECK" in dockerfile
    assert '${PORT:-7860}' in dockerfile
    assert "/_stcore/health" in dockerfile
    assert "127.0.0.1:8000/health" not in dockerfile


def test_persistence_settings_respect_runtime_environment(monkeypatch) -> None:
    monkeypatch.setenv(
        "CROPTWIN_DATABASE_URL",
        "postgresql+psycopg://fake_user:fake_password@db.internal:5432/croptwin",
    )
    monkeypatch.setenv("CROPTWIN_STATE_STORE", "memory")
    monkeypatch.setenv("CROPTWIN_AUTO_CREATE_DB", "false")

    settings = get_persistence_settings()

    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.normalized_state_store == "memory"
    assert settings.auto_create_db is False


def test_persistence_settings_local_defaults(monkeypatch) -> None:
    monkeypatch.delenv("CROPTWIN_DATABASE_URL", raising=False)
    monkeypatch.delenv("CROPTWIN_STATE_STORE", raising=False)
    monkeypatch.delenv("CROPTWIN_AUTO_CREATE_DB", raising=False)

    settings = get_persistence_settings()

    assert settings.database_url == DEFAULT_DATABASE_URL
    assert settings.normalized_state_store == "sqlalchemy"
    assert settings.auto_create_db is True


def test_safe_startup_summary_redacts_database_credentials(monkeypatch) -> None:
    monkeypatch.setenv(
        "CROPTWIN_DATABASE_URL",
        "postgresql+psycopg://fake_user:fake_password@db.internal:5432/croptwin",
    )
    monkeypatch.setenv("CROPTWIN_STATE_STORE", "sqlalchemy")
    monkeypatch.setenv("CROPTWIN_AUTO_CREATE_DB", "false")

    summary = persistence_startup_summary(get_persistence_settings())

    assert summary == (
        "CropTwin persistence: "
        "store=sqlalchemy dialect=postgresql auto_create=false"
    )
    assert "fake_user" not in summary
    assert "fake_password" not in summary
    assert "db.internal" not in summary
    assert "croptwin" not in summary
    assert "postgresql+psycopg://" not in summary


def test_alembic_env_uses_runtime_database_url_setting() -> None:
    source = ALEMBIC_ENV.read_text(encoding="utf-8")

    assert "get_persistence_settings" in source
    assert 'config.set_main_option("sqlalchemy.url", settings.database_url)' in source
    assert "url=settings.database_url" in source


def test_committed_compose_file_does_not_contain_postgres_password_value() -> None:
    compose = COMPOSE_FILE.read_text(encoding="utf-8")

    assert "croptwin_dev_password" not in compose
    assert "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:" in compose
