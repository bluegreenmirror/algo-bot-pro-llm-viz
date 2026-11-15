"""Headless Streamlit runs of the dashboard script (no browser needed)."""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "src" / "dashboard" / "app.py")


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    monkeypatch.delenv("DASHBOARD_ALLOW_BROKER", raising=False)
    return tmp_path


def _run() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception, [e.message for e in at.exception]
    return at


def _button(at: AppTest, label: str):
    return next(b for b in at.button if b.label == label)


def test_dashboard_defaults_to_mock_only(app):
    at = _run()
    assert at.sidebar.selectbox[0].options == ["mock"]
    assert any("DASHBOARD_ALLOW_BROKER" in c.value for c in at.sidebar.caption)


def test_dashboard_broker_modes_with_opt_in(app, monkeypatch):
    monkeypatch.setenv("DASHBOARD_ALLOW_BROKER", "true")
    at = _run()
    assert at.sidebar.selectbox[0].options == ["mock", "paper", "live"]


def test_equity_path_outside_logs_refused(app):
    outside = app / "outside.jsonl"
    outside.write_text('{"ts":1,"side":"buy","price":1,"notional":1,"symbol":"X"}\n')
    at = _run()
    path_input = next(t for t in at.text_input if t.label == "Backtest JSONL path")
    path_input.set_value(str(outside)).run()
    _button(at, "Load Equity Curve").click().run()
    assert any("inside logs/" in e.value for e in at.error)


def test_equity_curve_from_logs_file(app):
    (app / "logs" / "backtest_AAPL.jsonl").write_text(
        '{"ts":1,"side":"buy","price":100,"notional":1000,"symbol":"AAPL"}\n'
        '{"ts":5,"side":"sell","price":110,"notional":1000,"symbol":"AAPL"}\n'
    )
    at = _run()
    _button(at, "Load Equity Curve").click().run()
    assert not at.error
    assert not at.warning
