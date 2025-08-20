from __future__ import annotations
from typing import List

def sma(values: List[float], window: int) -> List[float]:
    if window <= 0: raise ValueError("window must be > 0")
    if len(values) < window: return []
    out = []; s = sum(values[:window]); out.append(s / window)
    for i in range(window, len(values)):
        s += values[i] - values[i - window]
        out.append(s / window)
    return out

def sma_signal(closes: List[float], fast: int, slow: int) -> str:
    if slow <= fast: raise ValueError("slow must be > fast")
    if len(closes) < slow + 1: return "none"
    f = sma(closes, fast); s = sma(closes, slow); diff = len(f) - len(s); f = f[diff:]
    if len(f) < 2 or len(s) < 2: return "none"
    prev = f[-2] - s[-2]; curr = f[-1] - s[-1]
    if prev <= 0 and curr > 0: return "buy"
    if prev >= 0 and curr < 0: return "sell"
    return "none"

def score_from_signal(signal: str) -> float:
    return {"buy": 0.7, "sell": 0.3, "none": 0.5}.get(signal, 0.5)

def blend_scores(sma_score: float, llm_score: float, w: float = 0.5) -> float:
    w = max(0.0, min(1.0, w))
    return (1 - w) * sma_score + w * llm_score
