from datetime import datetime
from src.compliance.engine import ComplianceEngine
from src.config import Settings


def test_weekend_blocked():
    settings = Settings()
    settings.symbols = ["AAPL"]
    engine = ComplianceEngine(settings=settings)
    saturday = datetime(2026, 11, 14, 12, 0)  # Saturday
    result = engine.check_all("AAPL", now=saturday)
    assert result.ok is False
    assert "weekend" in result.reason


def test_weekday_in_hours_ok():
    settings = Settings()
    settings.symbols = ["AAPL"]
    settings.trading_hours = "09:30-16:00"
    engine = ComplianceEngine(settings=settings)
    tuesday = datetime(2026, 11, 10, 10, 0)  # Tuesday
    result = engine.check_all("AAPL", now=tuesday)
    assert result.ok is True
