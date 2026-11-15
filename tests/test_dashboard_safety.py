import pytest
from src.dashboard.safety import allowed_modes, resolve_backtest_path


def test_dashboard_mock_only_by_default(monkeypatch):
    monkeypatch.delenv("DASHBOARD_ALLOW_BROKER", raising=False)
    assert allowed_modes() == ["mock"]
    monkeypatch.setenv("DASHBOARD_ALLOW_BROKER", "yes")
    assert allowed_modes() == ["mock"]


def test_dashboard_broker_modes_need_opt_in(monkeypatch):
    monkeypatch.setenv("DASHBOARD_ALLOW_BROKER", "true")
    assert allowed_modes() == ["mock", "paper", "live"]


def test_backtest_path_inside_logs_allowed(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    resolved = resolve_backtest_path("logs/backtest_AAPL.jsonl")
    assert resolved == tmp_path / "logs" / "backtest_AAPL.jsonl"


@pytest.mark.parametrize("path", [
    "../logs/backtest.jsonl",
    "logs/../.env",
    "logs/../secrets.jsonl",
    "/etc/passwd",
    "logs/notes.txt",
])
def test_backtest_path_outside_logs_refused(monkeypatch, tmp_path, path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    with pytest.raises(ValueError):
        resolve_backtest_path(path)


def test_backtest_symlink_escape_refused(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    (tmp_path / "secret.jsonl").write_text("{}")
    (tmp_path / "logs" / "link.jsonl").symlink_to(tmp_path / "secret.jsonl")
    with pytest.raises(ValueError):
        resolve_backtest_path("logs/link.jsonl")
