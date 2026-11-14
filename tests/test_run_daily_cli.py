from click.testing import CliRunner
from src.app import cli


def test_run_daily_defaults_to_mock_mode(monkeypatch):
    monkeypatch.delenv("ENABLE_TRADING", raising=False)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run-daily",
            "--universe", "AAPL",
            "--limit", "40",
            "--fast", "5",
            "--slow", "20",
            "--risk", "0.01",
            "--mode", "mock",
        ],
    )
    assert result.exit_code == 0, result.output
    assert '"mode": "mock"' in result.output


def test_run_daily_paper_without_keys_fails():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run-daily", "--universe", "AAPL", "--mode", "paper"],
        env={"ALPACA_KEY_ID": "", "ALPACA_SECRET_KEY": ""},
    )
    assert result.exit_code != 0
