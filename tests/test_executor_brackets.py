import pytest
from src.execution.executor import run_daily


class Ok:
    ok = True
    reason = "ok"


class No:
    ok = False
    reason = "notional>2000.0"


@pytest.fixture
def open_gates(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("src.execution.executor.PolicyEngine.check_all", lambda self, **kw: Ok())
    monkeypatch.setattr("src.execution.executor.ComplianceEngine.check_all", lambda self, **kw: Ok())


def _force_signal(monkeypatch, signal):
    monkeypatch.setattr("src.execution.executor.sma_signal", lambda closes, fast, slow: signal)


def _run(submit_fn, max_positions=1):
    closes = [100.0 + i for i in range(40)]
    return closes, run_daily(
        ["AAPL"],
        {"AAPL": closes},
        fast=5,
        slow=20,
        risk_per_trade=0.01,
        stop_loss_pct=0.03,
        take_profit_pct=0.05,
        max_positions=max_positions,
        submit_fn=submit_fn,
    )


def test_run_daily_passes_stop_take_to_submit(monkeypatch, open_gates):
    """REVISION_V1 v1.0: stop / take-profit flow into bracket orders."""
    captured = {}

    def fake_submit(symbol, *, notional, side, take_profit_pct, stop_loss_pct, ref_price):
        captured.update(symbol=symbol, notional=notional, side=side,
                        take_profit_pct=take_profit_pct, stop_loss_pct=stop_loss_pct,
                        ref_price=ref_price)
        return {"id": "ord_test", "status": "accepted"}

    _force_signal(monkeypatch, "buy")
    closes, result = _run(fake_submit)
    assert result["results"]["AAPL"]["action"] == "placed"
    assert captured["take_profit_pct"] == 0.05
    assert captured["stop_loss_pct"] == 0.03
    assert captured["ref_price"] == closes[-1]
    assert captured["side"] == "buy"


def test_run_daily_blocks_when_submit_none(monkeypatch, open_gates):
    """Kill-switch off: buy signal is recorded but not submitted."""
    _force_signal(monkeypatch, "buy")
    _, result = _run(None)
    assert result["results"]["AAPL"]["action"] == "blocked"
    assert "trading disabled" in result["results"]["AAPL"]["block_reason"]


@pytest.mark.parametrize("signal", ["sell", "none"])
def test_non_buy_signals_never_submit(monkeypatch, open_gates, signal):
    """Long-only: without tracked positions a sell would open a short."""
    calls = []
    _force_signal(monkeypatch, signal)
    _, result = _run(lambda *a, **kw: calls.append((a, kw)))
    decision = result["results"]["AAPL"]
    assert calls == []
    assert decision["action"] == "skipped"
    assert decision["signal"] == signal


def test_policy_block_prevents_submit(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("src.execution.executor.PolicyEngine.check_all", lambda self, **kw: No())
    monkeypatch.setattr("src.execution.executor.ComplianceEngine.check_all", lambda self, **kw: Ok())
    _force_signal(monkeypatch, "buy")
    calls = []
    _, result = _run(lambda *a, **kw: calls.append(1))
    assert calls == []
    assert result["results"]["AAPL"]["block_reason"] == No.reason
