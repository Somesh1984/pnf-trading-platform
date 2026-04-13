from __future__ import annotations

from trading_app.config import AppConfig
from trading_app.health import check_questdb_health, questdb_health_url


class FakeResponse:
    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_questdb_health_url_is_built_from_config() -> None:
    config = AppConfig(questdb_host="questdb.local", questdb_http_port=19000)

    assert questdb_health_url(config) == "http://questdb.local:19000/exec?query=select%201"


def test_health_checker_handles_success_response() -> None:
    calls: list[tuple[str, float]] = []

    def opener(url: str, timeout: float) -> FakeResponse:
        calls.append((url, timeout))
        return FakeResponse(status=200)

    config = AppConfig()
    result = check_questdb_health(config, timeout=1.5, opener=opener)

    assert result.ok is True
    assert result.detail == "HTTP 200"
    assert calls == [("http://localhost:19000/exec?query=select%201", 1.5)]


def test_health_checker_handles_failure_without_crashing() -> None:
    def opener(url: str, timeout: float) -> FakeResponse:
        raise OSError("connection refused")

    result = check_questdb_health(AppConfig(), opener=opener)

    assert result.ok is False
    assert "connection refused" in result.detail
