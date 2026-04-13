from __future__ import annotations

from dataclasses import dataclass
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import urlopen

from trading_app.config import AppConfig


@dataclass(frozen=True)
class HealthCheckResult:
    ok: bool
    url: str
    detail: str


def questdb_health_url(config: AppConfig) -> str:
    query = quote("select 1", safe="")
    return f"{config.questdb_http_url}/exec?query={query}"


def check_questdb_health(
    config: AppConfig,
    timeout: float = 2.0,
    opener=urlopen,
) -> HealthCheckResult:
    url = questdb_health_url(config)
    try:
        with opener(url, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            if 200 <= status < 300:
                return HealthCheckResult(ok=True, url=url, detail=f"HTTP {status}")
            return HealthCheckResult(ok=False, url=url, detail=f"HTTP {status}")
    except (OSError, URLError) as exc:
        return HealthCheckResult(ok=False, url=url, detail=str(exc))
