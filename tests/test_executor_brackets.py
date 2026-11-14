from src.execution.executor import run_daily


def test_run_daily_passes_stop_take_to_submit(monkeypatch):
    captured = {}

    def fake_submit(symbol, *, notional, side, take_profit_pct, stop_loss_pct, ref_price):
        captured.update({
            "symbol": symbol,
            "notional": notional,
            "side": side,
            "take_profit_pct": take_profit_pct,
            "stop_loss_pct": stop_loss_pct,
            "ref_price": ref_price,
        })
        return {"id": "ord_test", "status": "accepted"}

    # Force compliance/policy open by patching engines
    class Ok:
        ok = True
        reason = "ok"

    monkeypatch.setattr("src.execution.executor.PolicyEngine.check_all", lambda self, **kw: Ok())
    monkeypatch.setattr("src.execution.executor.ComplianceEngine.check_all", lambda self, **kw: Ok())
    monkeypatch.setattr(
        "src.execution.executor.sma_signal",
        lambda closes, fast, slow: "buy",
    )

    closes = [100.0 + i for i in range(40)]
    result = run_daily(
        ["AAPL"],
        {"AAPL": closes},
        fast=5,
        slow=20,
        risk_per_trade=0.01,
        stop_loss_pct=0.03,
        take_profit_pct=0.05,
        max_positions=1,
        submit_fn=fake_submit,
    )
    assert result["results"]["AAPL"]["action"] == "placed"
    assert captured["take_profit_pct"] == 0.05
    assert captured["stop_loss_pct"] == 0.03
    assert captured["ref_price"] == closes[-1]
    assert captured["side"] == "buy"


def test_run_daily_blocks_when_submit_none(monkeypatch):
    class Ok:
        ok = True
        reason = "ok"

    monkeypatch.setattr("src.execution.executor.PolicyEngine.check_all", lambda self, **kw: Ok())
    monkeypatch.setattr("src.execution.executor.ComplianceEngine.check_all", lambda self, **kw: Ok())

    closes = [100.0 + i for i in range(40)]
    result = run_daily(
        ["AAPL"],
        {"AAPL": closes},
        fast=5,
        slow=20,
        risk_per_trade=0.01,
        stop_loss_pct=0.03,
        take_profit_pct=0.05,
        max_positions=1,
        submit_fn=None,
    )
    assert result["results"]["AAPL"]["action"] == "blocked"
    assert "trading disabled" in result["results"]["AAPL"]["block_reason"]
