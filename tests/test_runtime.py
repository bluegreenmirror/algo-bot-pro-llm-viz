import os
import pytest
from src.runtime import is_trading_enabled, resolve_mode


def test_trading_enabled_only_when_explicit_true(monkeypatch):
    monkeypatch.delenv("ENABLE_TRADING", raising=False)
    assert is_trading_enabled() is False
    monkeypatch.setenv("ENABLE_TRADING", "false")
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
