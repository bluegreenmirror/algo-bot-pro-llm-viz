from __future__ import annotations
from dataclasses import dataclass
import hashlib, json, os
from typing import Dict, Any, Optional

SUPPORTED_PROVIDERS = ("mock",)

@dataclass
class ScoreResponse:
    score: float
    rationale: str
    model: str

_CACHE: Dict[str, ScoreResponse] = {}

def _cache_key(symbol: str, features: Dict[str, Any], model: str) -> str:
    js = json.dumps({"s":symbol, "f":features, "m":model}, sort_keys=True)
    return hashlib.sha256(js.encode()).hexdigest()

def _prompt(symbol: str, features: Dict[str, Any]) -> str:
    return (
        "You are a research assistant scoring a single equity opportunity.\n"
        "Return a score 0..1 for attractiveness over next 1-5 sessions.\n"
        "Use only provided features; do not invent data. Keep rationale <120 chars.\n\n"
        f"SYMBOL: {symbol}\nFEATURES: {json.dumps(features, sort_keys=True)}\n"
        f"OUTPUT JSON: {{\"score\": float 0..1, \"rationale\": str}}\n"
    )

def _mock_call(prompt: str, model: str, timeout: int) -> Dict[str, Any]:
    h = int(hashlib.sha256(prompt.encode()).hexdigest(), 16) % 100
    score = max(0.0, min(1.0, 0.4 + (h/1000.0)))
    return {"score": round(score, 3), "rationale": "Score blended from technical/context."}

def score(symbol: str, features: Dict[str, Any], *, provider: Optional[str]=None, model: Optional[str]=None, timeout: Optional[int]=None, use_cache: bool=True) -> ScoreResponse:
    """
    Score one symbol. Only the deterministic mock provider exists in v1.x;
    real providers arrive with LLM shadow mode (REVISION_V1 v1.2) and are
    rejected here so no prompt or key leaves the process by accident.
    """
    provider = (provider or os.getenv("LLM_PROVIDER", "mock")).strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"LLM_PROVIDER={provider!r} is not supported yet; use 'mock' "
            "(real providers are planned for v1.2 shadow mode)"
        )
    model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
    timeout = int(timeout or os.getenv("LLM_TIMEOUT", "10"))
    ck = _cache_key(symbol, features, model)
    if use_cache and ck in _CACHE:
        return _CACHE[ck]
    raw = _mock_call(_prompt(symbol, features), model, timeout)
    resp = ScoreResponse(score=float(raw["score"]), rationale=raw["rationale"], model=model)
    if use_cache: _CACHE[ck] = resp
    return resp
