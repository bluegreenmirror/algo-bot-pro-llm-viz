import json
from types import SimpleNamespace
import pytest
from click.testing import CliRunner
from src.app import cli

PAPER_ENV = {
    "ALPACA_KEY_ID": "test-key",
    "ALPACA_SECRET_KEY": "test-secret",
    "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
    "SYMBOLS": "AAPL",
}


@pytest.fixture(autouse=True)
def isolated_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)


def test_run_daily_defaults_to_mock_mode(monkeypatch):
    monkeypatch.delenv("ENABLE_TRADING", raising=False)
    result = CliRunner().invoke(
        cli,
        ["run-daily", "--universe", "AAPL", "--limit", "40", "--fast", "5", "--slow", "20", "--risk", "0.01"],
    )
    assert result.exit_code == 0, result.output
    assert '"mode": "mock"' in result.output


def test_run_daily_paper_without_keys_fails():
    result = CliRunner().invoke(
        cli,
        ["run-daily", "--universe", "AAPL", "--mode", "paper"],
        env={"ALPACA_KEY_ID": "", "ALPACA_SECRET_KEY": ""},
    )
    assert result.exit_code != 0


def test_run_daily_paper_refuses_live_endpoint():
    result = CliRunner().invoke(
        cli,
        ["run-daily", "--universe", "AAPL", "--mode", "paper"],
        env={**PAPER_ENV, "ALPACA_BASE_URL": "https://api.alpaca.markets"},
    )
    assert result.exit_code != 0
    assert "paper mode requires" in result.output


def test_run_daily_paper_kill_switch_off_never_submits(monkeypatch):
    """SECURITY.md: unset ENABLE_TRADING means dry run; the broker is never called."""
    closes = [100.0 + i for i in range(40)]
    monkeypatch.setattr(
        "src.data.providers.alpaca.fetch_bars",
        lambda symbol, limit, client=None: [SimpleNamespace(c=c) for c in closes],
    )
    monkeypatch.setattr("src.execution.executor.sma_signal", lambda closes, fast, slow: "buy")

    class Ok:
        ok = True
        reason = "ok"

    monkeypatch.setattr("src.execution.executor.PolicyEngine.check_all", lambda self, **kw: Ok())
    monkeypatch.setattr("src.execution.executor.ComplianceEngine.check_all", lambda self, **kw: Ok())
    calls = []
    monkeypatch.setattr("src.broker.alpaca_client.submit_bracket_order", lambda *a, **kw: calls.append(1))

    result = CliRunner().invoke(
        cli,
        ["run-daily", "--universe", "AAPL", "--mode", "paper"],
        env={**PAPER_ENV, "ENABLE_TRADING": ""},
    )
    assert result.exit_code == 0, result.output
    assert calls == []
    payload = json.loads(result.output.strip().splitlines()[-1])
    assert payload["mode"] == "paper"
    assert payload["results"]["AAPL"]["action"] == "blocked"


def test_run_daily_unsupported_llm_provider_is_usage_error():
    result = CliRunner().invoke(
        cli,
        ["run-daily", "--universe", "AAPL", "--mode", "mock"],
        env={"LLM_PROVIDER": "openai"},
    )
    assert result.exit_code == 2
    assert "not supported" in result.output
