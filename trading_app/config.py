from __future__ import annotations

"""Runtime config loading for the local trading app.

Read order:
1. explicit `load_config(env=...)` input
2. local `.env` file
3. current shell environment, which overrides `.env`
"""

from dataclasses import asdict, dataclass
from os import environ
from pathlib import Path
from typing import Mapping


# Paths and secret field names used by config output.
DEFAULT_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
SECRET_FIELDS = frozenset(
    {
        "fyers_secret_key",
        "fyers_access_token",
        "telegram_bot_token",
    }
)


# Small parsing helpers used by `load_config()`.
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


def _strip_optional_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _load_dotenv_file(path: Path) -> dict[str, str]:
    """Read a simple KEY=VALUE .env file without external dependencies."""
    if not path.is_file():
        return {}

    values: dict[str, str] = {}
    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            raise ValueError(f"Invalid .env line {lineno}: expected KEY=VALUE")

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Invalid .env line {lineno}: missing key")

        values[key] = _strip_optional_quotes(value.strip())

    return values


def _build_env_source(env: Mapping[str, str] | None) -> Mapping[str, str]:
    """Build the final config source with clear override order."""
    if env is not None:
        return env

    source = _load_dotenv_file(DEFAULT_ENV_PATH)
    source.update(environ)
    return source


@dataclass(frozen=True)
class AppConfig:
    """Strongly-typed runtime config used by CLI and app services."""

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
    def fyers_auth_configured(self) -> bool:
        return all(
            (
                self.fyers_client_id,
                self.fyers_secret_key,
                self.fyers_redirect_uri,
            )
        )

    @property
    def fyers_access_token_configured(self) -> bool:
        return bool(self.fyers_access_token)

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
    """Load config from explicit env, `.env`, and shell environment."""
    source = _build_env_source(env)
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
    """Keep basic runtime settings valid before the app starts."""
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
    """Return config data safe for CLI/debug output."""
    data = asdict(config)
    for field in SECRET_FIELDS:
        if data.get(field):
            data[field] = "***"
    return data
