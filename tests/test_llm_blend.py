from src.strategy.sma import blend_scores
def test_blend_scores():
    assert blend_scores(0.5, 1.0, w=0.4) > 0.5
    assert blend_scores(0.7, 0.2, w=0.5) < 0.7
