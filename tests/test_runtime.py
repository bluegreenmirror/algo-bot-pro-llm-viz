import pytest
from src.runtime import is_trading_enabled, require_endpoint_for_mode, resolve_mode


def test_trading_enabled_only_when_explicit_true(monkeypatch):
    monkeypatch.delenv("ENABLE_TRADING", raising=False)
    assert is_trading_enabled() is False
    monkeypatch.setenv("ENABLE_TRADING", "false")
    assert is_trading_enabled() is False
    monkeypatch.setenv("ENABLE_TRADING", "1")
    assert is_trading_enabled() is False
    monkeypatch.setenv("ENABLE_TRADING", "true")
    assert is_trading_enabled() is True
    monkeypatch.setenv("ENABLE_TRADING", "TRUE")
    assert is_trading_enabled() is True


def test_resolve_mode_defaults_and_aliases():
    assert resolve_mode() == "mock"
    assert resolve_mode(mock=True) == "mock"
    assert resolve_mode(live=True) == "paper"
    assert resolve_mode("paper") == "paper"
    assert resolve_mode("live") == "live"
    with pytest.raises(ValueError):
        resolve_mode(mock=True, live=True)
    with pytest.raises(ValueError):
        resolve_mode("paper", mock=True)
    with pytest.raises(ValueError):
        resolve_mode("prod")


@pytest.mark.parametrize("mode,url", [
    ("paper", "https://paper-api.alpaca.markets"),
    ("paper", "https://paper-api.alpaca.markets/"),
    ("live", "https://api.alpaca.markets"),
    ("mock", "https://api.alpaca.markets"),
])
def test_endpoint_matches_mode(mode, url):
    """SECURITY.md: separate endpoints for paper and live."""
    require_endpoint_for_mode(mode, url)


@pytest.mark.parametrize("mode,url", [
    ("paper", "https://api.alpaca.markets"),
    ("live", "https://paper-api.alpaca.markets"),
    ("paper", "http://paper-api.alpaca.markets"),
    ("paper", "https://paper-api.alpaca.markets.evil.example"),
    ("live", "https://evil.example/api.alpaca.markets"),
    ("live", ""),
])
def test_endpoint_mismatch_refused(mode, url):
    """Paper can never reach live, live never silently runs on paper, HTTPS only."""
    with pytest.raises(RuntimeError):
        require_endpoint_for_mode(mode, url)


def test_endpoint_defaults_to_paper(monkeypatch):
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    require_endpoint_for_mode("paper")
    with pytest.raises(RuntimeError):
        require_endpoint_for_mode("live")
