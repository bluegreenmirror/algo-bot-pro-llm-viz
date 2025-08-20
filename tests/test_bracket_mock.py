from src.sim.broker.fake_broker import submit_bracket_order

def test_submit_bracket_order_mock():
    result = submit_bracket_order("AAPL", notional=100, side="buy", take_profit_pct=0.05, stop_loss_pct=0.03)
    assert result.status == "accepted"
    assert result.symbol == "AAPL"
    assert result.side == "buy"
    assert result.notional == 100
    assert result.take_profit_pct == 0.05
    assert result.stop_loss_pct == 0.03
