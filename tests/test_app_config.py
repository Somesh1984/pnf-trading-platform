from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

import trading_app.config as config_module
from trading_app.config import load_config, redacted_config


def _workspace_env_file(content: str) -> Path:
    env_dir = Path("runtime") / "test-config"
    env_dir.mkdir(parents=True, exist_ok=True)
    env_file = env_dir / f"{uuid4().hex}.env"
    env_file.write_text(content, encoding="utf-8")
    return env_file


def test_defaults_load_without_secrets() -> None:
    config = load_config({})

    assert config.app_env == "development"
    assert config.log_level == "INFO"
    assert config.trading_mode == "paper"
    assert config.live_trading_enabled is False
    assert config.questdb_http_url == "http://localhost:19000"
    assert config.questdb_ilp_address == "localhost:19009"
    assert config.questdb_pg_address == "localhost:18812"
    assert config.fyers_client_id == ""
    assert config.telegram_bot_token == ""


def test_environment_overrides_defaults() -> None:
    config = load_config(
        {
            "APP_ENV": "test",
            "LOG_LEVEL": "debug",
            "TRADING_MODE": "live",
            "LIVE_TRADING_ENABLED": "true",
            "QUESTDB_HOST": "questdb.local",
            "QUESTDB_HTTP_PORT": "19000",
            "QUESTDB_ILP_PORT": "19009",
            "QUESTDB_PG_PORT": "18812",
            "FYERS_CLIENT_ID": " client ",
            "FYERS_SECRET_KEY": " secret ",
            "FYERS_REDIRECT_URI": " https://example.test/callback ",
            "FYERS_ACCESS_TOKEN": " token ",
            "TELEGRAM_CHAT_ID": "chat",
        }
    )

    assert config.app_env == "test"
    assert config.log_level == "DEBUG"
    assert config.trading_mode == "live"
    assert config.live_trading_enabled is True
    assert config.questdb_http_url == "http://questdb.local:19000"
    assert config.questdb_ilp_address == "questdb.local:19009"
    assert config.questdb_pg_address == "questdb.local:18812"
    assert config.fyers_client_id == "client"
    assert config.fyers_secret_key == "secret"
    assert config.fyers_redirect_uri == "https://example.test/callback"
    assert config.fyers_access_token == "token"
    assert config.fyers_auth_configured is True
    assert config.fyers_access_token_configured is True
    assert config.telegram_chat_id == "chat"


def test_live_trading_defaults_to_disabled() -> None:
    config = load_config({"TRADING_MODE": "paper"})

    assert config.live_trading_enabled is False


def test_missing_fyers_and_telegram_secrets_do_not_fail_m1_config() -> None:
    config = load_config({})

    assert config.fyers_secret_key == ""
    assert config.fyers_access_token == ""
    assert config.fyers_auth_configured is False
    assert config.fyers_access_token_configured is False
    assert config.telegram_bot_token == ""


def test_live_enabled_requires_live_mode() -> None:
    with pytest.raises(ValueError, match="LIVE_TRADING_ENABLED"):
        load_config({"TRADING_MODE": "paper", "LIVE_TRADING_ENABLED": "true"})


def test_redacted_config_masks_secret_values() -> None:
    config = load_config(
        {
            "FYERS_CLIENT_ID": "client-id",
            "FYERS_SECRET_KEY": "secret",
            "FYERS_REDIRECT_URI": "https://example.test/callback",
            "FYERS_ACCESS_TOKEN": "token",
            "TELEGRAM_BOT_TOKEN": "bot-token",
        }
    )

    redacted = redacted_config(config)

    assert redacted["fyers_client_id"] == "client-id"
    assert redacted["fyers_secret_key"] == "***"
    assert redacted["fyers_redirect_uri"] == "https://example.test/callback"
    assert redacted["fyers_access_token"] == "***"
    assert redacted["telegram_bot_token"] == "***"


def test_partial_fyers_auth_config_is_not_marked_ready() -> None:
    config = load_config(
        {
            "FYERS_CLIENT_ID": "client-id",
            "FYERS_REDIRECT_URI": "https://example.test/callback",
        }
    )

    assert config.fyers_auth_configured is False
    assert config.fyers_access_token_configured is False


def test_dotenv_values_load_when_no_explicit_env(monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = _workspace_env_file(
        "\n".join(
            [
                "APP_ENV=local",
                "FYERS_CLIENT_ID=file-client",
                "FYERS_SECRET_KEY=file-secret",
                'FYERS_REDIRECT_URI="https://file.example/callback"',
                "FYERS_ACCESS_TOKEN=file-token",
            ]
        )
    )
    monkeypatch.setattr(config_module, "DEFAULT_ENV_PATH", env_file)
    for key in (
        "APP_ENV",
        "FYERS_CLIENT_ID",
        "FYERS_SECRET_KEY",
        "FYERS_REDIRECT_URI",
        "FYERS_ACCESS_TOKEN",
    ):
        monkeypatch.delenv(key, raising=False)

    config = load_config()

    assert config.app_env == "local"
    assert config.fyers_client_id == "file-client"
    assert config.fyers_secret_key == "file-secret"
    assert config.fyers_redirect_uri == "https://file.example/callback"
    assert config.fyers_access_token == "file-token"
    assert config.fyers_auth_configured is True
    assert config.fyers_access_token_configured is True


def test_os_environ_overrides_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = _workspace_env_file(
        "\n".join(
            [
                "APP_ENV=file-env",
                "FYERS_CLIENT_ID=file-client",
            ]
        )
    )
    monkeypatch.setattr(config_module, "DEFAULT_ENV_PATH", env_file)
    monkeypatch.setenv("APP_ENV", "shell-env")
    monkeypatch.setenv("FYERS_CLIENT_ID", "shell-client")

    config = load_config()

    assert config.app_env == "shell-env"
    assert config.fyers_client_id == "shell-client"


def test_explicit_env_bypasses_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = _workspace_env_file("FYERS_CLIENT_ID=file-client\n")
    monkeypatch.setattr(config_module, "DEFAULT_ENV_PATH", env_file)

    config = load_config({"FYERS_CLIENT_ID": "direct-client"})

    assert config.fyers_client_id == "direct-client"


def test_missing_dotenv_still_uses_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module, "DEFAULT_ENV_PATH", Path("runtime") / "test-config" / "missing.env")
    monkeypatch.delenv("APP_ENV", raising=False)

    config = load_config()

    assert config.app_env == "development"
    assert config.fyers_client_id == ""


def test_invalid_dotenv_line_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = _workspace_env_file("NOT_A_VALID_LINE\n")
    monkeypatch.setattr(config_module, "DEFAULT_ENV_PATH", env_file)

    with pytest.raises(ValueError, match=r"Invalid \.env line 1"):
        load_config()
