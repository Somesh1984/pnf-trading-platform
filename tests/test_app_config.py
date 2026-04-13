from __future__ import annotations

import pytest

from trading_app.config import load_config, redacted_config


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
            "FYERS_CLIENT_ID": "client",
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
    assert config.telegram_chat_id == "chat"


def test_live_trading_defaults_to_disabled() -> None:
    config = load_config({"TRADING_MODE": "paper"})

    assert config.live_trading_enabled is False


def test_missing_fyers_and_telegram_secrets_do_not_fail_m1_config() -> None:
    config = load_config({})

    assert config.fyers_secret_key == ""
    assert config.fyers_access_token == ""
    assert config.telegram_bot_token == ""


def test_live_enabled_requires_live_mode() -> None:
    with pytest.raises(ValueError, match="LIVE_TRADING_ENABLED"):
        load_config({"TRADING_MODE": "paper", "LIVE_TRADING_ENABLED": "true"})


def test_redacted_config_masks_secret_values() -> None:
    config = load_config(
        {
            "FYERS_SECRET_KEY": "secret",
            "FYERS_ACCESS_TOKEN": "token",
            "TELEGRAM_BOT_TOKEN": "bot-token",
        }
    )

    redacted = redacted_config(config)

    assert redacted["fyers_secret_key"] == "***"
    assert redacted["fyers_access_token"] == "***"
    assert redacted["telegram_bot_token"] == "***"
