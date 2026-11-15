"""place-bracket must pass the same policy, compliance and endpoint gates as run-daily."""
import pytest
from click.testing import CliRunner
from src.app import cli

PAPER_ENV = {
    "ENABLE_TRADING": "true",
    "ALPACA_KEY_ID": "test-key",
    "ALPACA_SECRET_KEY": "test-secret",
    "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
    "SYMBOLS": "AAPL",
    "MAX_NOTIONAL": "2000",
}


class Ok:
    ok = True
    reason = "ok"


@pytest.fixture
def broker_calls(monkeypatch):
    calls = []

    def fake_submit(**kwargs):
        calls.append(kwargs)
        return {"id": "ord_paper", "status": "accepted"}

    monkeypatch.setattr("src.broker.alpaca_client.submit_bracket_order", fake_submit)
    return calls


def _invoke(args, env):
    return CliRunner().invoke(cli, ["place-bracket", "--symbol", "AAPL", "--side", "buy", *args], env=env)


def test_mock_notional_over_max_blocked_by_policy():
    result = _invoke(["--notional", "5000", "--ref-price", "150"], {"MAX_NOTIONAL": "2000"})
    assert result.exit_code != 0
    assert "Blocked by policy" in result.output


def test_qty_requires_ref_price():
    result = _invoke(["--qty", "10"], {})
    assert result.exit_code != 0
    assert "--ref-price is required" in result.output


def test_qty_times_ref_price_checked_against_policy():
    result = _invoke(["--qty", "100", "--ref-price", "150"], {"MAX_NOTIONAL": "2000"})
    assert result.exit_code != 0
    assert "Blocked by policy" in result.output


def test_qty_and_notional_mutually_exclusive():
    result = _invoke(["--qty", "1", "--notional", "5", "--ref-price", "150"], {})
    assert result.exit_code != 0


def test_paper_requires_kill_switch(broker_calls):
    result = _invoke(["--notional", "5", "--ref-price", "150", "--mode", "paper"],
                     {**PAPER_ENV, "ENABLE_TRADING": "false"})
    assert result.exit_code != 0
    assert "ENABLE_TRADING" in result.output
    assert broker_calls == []


def test_paper_refuses_live_endpoint(broker_calls):
    result = _invoke(["--notional", "5", "--ref-price", "150", "--mode", "paper"],
                     {**PAPER_ENV, "ALPACA_BASE_URL": "https://api.alpaca.markets"})
    assert result.exit_code != 0
    assert "paper mode requires" in result.output
    assert broker_calls == []


def test_live_refuses_paper_endpoint(broker_calls):
    result = _invoke(["--notional", "5", "--ref-price", "150", "--mode", "live"], PAPER_ENV)
    assert result.exit_code != 0
    assert "live mode requires" in result.output
    assert broker_calls == []


def test_paper_blocked_by_compliance(broker_calls, monkeypatch):
    class Closed:
        ok = False
        reason = "outside trading hours"

    monkeypatch.setattr("src.compliance.engine.ComplianceEngine.check_all", lambda self, **kw: Closed())
    result = _invoke(["--notional", "5", "--ref-price", "150", "--mode", "paper"], PAPER_ENV)
    assert result.exit_code != 0
    assert "Blocked by compliance" in result.output
    assert broker_calls == []


def test_paper_happy_path_submits_bracket(broker_calls, monkeypatch):
    monkeypatch.setattr("src.compliance.engine.ComplianceEngine.check_all", lambda self, **kw: Ok())
    result = _invoke(["--notional", "5", "--ref-price", "150", "--tp", "0.06", "--sl", "0.02", "--mode", "paper"],
                     PAPER_ENV)
    assert result.exit_code == 0, result.output
    assert len(broker_calls) == 1
    call = broker_calls[0]
    assert call["take_profit_pct"] == 0.06
    assert call["stop_loss_pct"] == 0.02
    assert call["ref_price"] == 150
