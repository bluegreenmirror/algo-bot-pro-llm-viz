from datetime import datetime, timezone
import pytest
from src.compliance.engine import ComplianceEngine
from src.config import Settings


def _engine(**overrides) -> ComplianceEngine:
    settings = Settings()
    settings.symbols = ["AAPL"]
    settings.trading_hours = "09:30-16:00"
    settings.market_tz = "America/New_York"
    for key, value in overrides.items():
        setattr(settings, key, value)
    return ComplianceEngine(settings=settings)


def test_weekend_blocked():
    saturday = datetime(2026, 11, 14, 12, 0)
    result = _engine().check_all("AAPL", now=saturday)
    assert result.ok is False
    assert "weekend" in result.reason


def test_weekday_in_hours_ok():
    tuesday = datetime(2026, 11, 10, 10, 0)
    assert _engine().check_all("AAPL", now=tuesday).ok is True


def test_symbol_not_whitelisted_blocked():
    tuesday = datetime(2026, 11, 10, 10, 0)
    result = _engine().check_all("TSLA", now=tuesday)
    assert result.ok is False
    assert "not whitelisted" in result.reason


@pytest.mark.parametrize("utc_hour,utc_minute,expected_ok", [
    (14, 29, False),  # 09:29 ET
    (14, 30, True),   # 09:30 ET open
    (20, 59, True),   # 15:59 ET
    (21, 0, False),   # 16:00 ET close is excluded
])
def test_hours_use_market_timezone_not_host_utc(utc_hour, utc_minute, expected_ok):
    """A UTC container must evaluate 09:30-16:00 in America/New_York (EST = UTC-5)."""
    now = datetime(2026, 11, 10, utc_hour, utc_minute, tzinfo=timezone.utc)
    assert _engine().check_all("AAPL", now=now).ok is expected_ok


def test_weekday_uses_market_timezone():
    """Monday 01:00 UTC is still Sunday in New York."""
    monday_utc = datetime(2026, 11, 16, 1, 0, tzinfo=timezone.utc)
    result = _engine().check_weekday(now=monday_utc)
    assert result.ok is False


def test_default_now_is_market_local():
    now = _engine().market_now()
    assert now.tzinfo is not None
    assert str(now.tzinfo) == "America/New_York"
