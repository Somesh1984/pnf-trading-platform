from __future__ import annotations

from dataclasses import asdict, dataclass
from os import environ
from typing import Mapping


SECRET_FIELDS = {
    "fyers_secret_key",
    "fyers_access_token",
    "telegram_bot_token",
}


def _get_bool(env: Mapping[str, str], key: str, default: bool) -> bool:
    value = env.get(key)
    if value is None or value == "":
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(f"{key} must be a boolean value")


def _get_int(env: Mapping[str, str], key: str, default: int) -> int:
    value = env.get(key)
    if value is None or value == "":
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer") from exc


def _get_str(env: Mapping[str, str], key: str, default: str = "") -> str:
    return env.get(key, default).strip()


@dataclass(frozen=True)
class AppConfig:
    app_env: str = "development"
    log_level: str = "INFO"
    trading_mode: str = "paper"
    live_trading_enabled: bool = False
    questdb_host: str = "localhost"
    questdb_http_port: int = 19000
    questdb_ilp_port: int = 19009
    questdb_pg_port: int = 18812
    fyers_client_id: str = ""
    fyers_secret_key: str = ""
    fyers_redirect_uri: str = ""
    fyers_access_token: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    @property
    def questdb_http_url(self) -> str:
        return f"http://{self.questdb_host}:{self.questdb_http_port}"

    @property
    def questdb_ilp_address(self) -> str:
        return f"{self.questdb_host}:{self.questdb_ilp_port}"

    @property
    def questdb_pg_address(self) -> str:
        return f"{self.questdb_host}:{self.questdb_pg_port}"


def load_config(env: Mapping[str, str] | None = None) -> AppConfig:
    source = environ if env is None else env

    config = AppConfig(
        app_env=_get_str(source, "APP_ENV", "development"),
        log_level=_get_str(source, "LOG_LEVEL", "INFO").upper(),
        trading_mode=_get_str(source, "TRADING_MODE", "paper"),
        live_trading_enabled=_get_bool(source, "LIVE_TRADING_ENABLED", False),
        questdb_host=_get_str(source, "QUESTDB_HOST", "localhost"),
        questdb_http_port=_get_int(source, "QUESTDB_HTTP_PORT", 19000),
        questdb_ilp_port=_get_int(source, "QUESTDB_ILP_PORT", 19009),
        questdb_pg_port=_get_int(source, "QUESTDB_PG_PORT", 18812),
        fyers_client_id=_get_str(source, "FYERS_CLIENT_ID"),
        fyers_secret_key=_get_str(source, "FYERS_SECRET_KEY"),
        fyers_redirect_uri=_get_str(source, "FYERS_REDIRECT_URI"),
        fyers_access_token=_get_str(source, "FYERS_ACCESS_TOKEN"),
        telegram_bot_token=_get_str(source, "TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=_get_str(source, "TELEGRAM_CHAT_ID"),
    )
    validate_config(config)
    return config


def validate_config(config: AppConfig) -> None:
    if config.trading_mode not in {"paper", "live"}:
        raise ValueError("TRADING_MODE must be 'paper' or 'live'")

    if config.live_trading_enabled and config.trading_mode != "live":
        raise ValueError("LIVE_TRADING_ENABLED can be true only when TRADING_MODE=live")

    if config.questdb_http_port <= 0:
        raise ValueError("QUESTDB_HTTP_PORT must be positive")
    if config.questdb_ilp_port <= 0:
        raise ValueError("QUESTDB_ILP_PORT must be positive")
    if config.questdb_pg_port <= 0:
        raise ValueError("QUESTDB_PG_PORT must be positive")


def redacted_config(config: AppConfig) -> dict[str, object]:
    data = asdict(config)
    for field in SECRET_FIELDS:
        if data.get(field):
            data[field] = "***"
    return data
