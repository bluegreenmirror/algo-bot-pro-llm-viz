import pytest
from src.agent import llm


def test_mock_score_deterministic_and_bounded():
    a = llm.score("AAPL", {"n": 40}, provider="mock", use_cache=False)
    b = llm.score("AAPL", {"n": 40}, provider="mock", use_cache=False)
    assert a.score == b.score
    assert 0.0 <= a.score <= 1.0


@pytest.mark.parametrize("provider", ["openai", "anthropic", "unknown"])
def test_real_providers_rejected_until_v1_2(provider, monkeypatch):
    """No prompt or API key may leave the process before shadow mode exists."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    with pytest.raises(ValueError, match="not supported"):
        llm.score("AAPL", {"n": 40}, provider=provider, use_cache=False)
