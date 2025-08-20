# tests/test_bracket_cli.py
from click.testing import CliRunner
from src.app import cli

def test_cli_place_bracket_mock():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "place-bracket",
            "--symbol", "AAPL",
            "--side", "buy",
            "--notional", "5",
            "--tp", "0.06",
            "--sl", "0.03",
            "--ref-price", "150"
        ]
    )
    assert result.exit_code == 0, result.output
    out = result.output
    # Works with both echo styles:
    # - f"Placed bracket order: {order}"
    # - click.echo(rec) SimpleNamespace repr
    assert ("Placed bracket order" in out) or ("ord_mock_bracket" in out)
    assert "AAPL" in out
    assert "accepted" in out