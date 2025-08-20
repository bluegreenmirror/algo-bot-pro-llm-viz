from __future__ import annotations
from dataclasses import dataclass
import hashlib, json, os
from typing import Dict, Any, Optional

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
    provider = provider or os.getenv("LLM_PROVIDER", "mock")
    model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
    timeout = int(timeout or os.getenv("LLM_TIMEOUT", "10"))
    ck = _cache_key(symbol, features, model)
    if use_cache and ck in _CACHE:
        return _CACHE[ck]
    prompt = _prompt(symbol, features)
    if provider == "openai":
        raw = _call_openai(prompt, model, timeout)
    elif provider == "anthropic":
        raw = _call_anthropic(prompt, model, timeout)
    else:
        raw = _mock_call(prompt, model, timeout)
    raw = _mock_call(prompt, model, timeout)  # replace with provider call when ready
    resp = ScoreResponse(score=float(raw["score"]), rationale=raw["rationale"], model=model)
    if use_cache: _CACHE[ck] = resp
    return resp
# append/replace parts inside src/agent/llm.py

def _call_openai(prompt: str, model: str, timeout: int) -> Dict[str, Any]:
    try:
        import openai  # pip install openai
    except Exception as e:
        raise RuntimeError("OpenAI provider selected but 'openai' SDK not installed. pip install openai") from e
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY missing in environment.")
    openai.api_key = api_key
    # Minimal example; adapt to latest API as you prefer:
    # NOTE: This is a placeholder structure; you may need to adjust for the latest OpenAI client semantics.
    completion = openai.ChatCompletion.create(
        model=model,
        messages=[{"role":"system","content":"Return JSON only."},{"role":"user","content":prompt}],
        temperature=0.2,
        timeout=timeout,
    )
    text = completion["choices"][0]["message"]["content"]
    try:
        data = json.loads(text)
        return {"score": float(data["score"]), "rationale": str(data["rationale"])}
    except Exception:
        # fallback: heuristic parse
        return {"score": 0.5, "rationale": "OpenAI: parse fallback"}

def _call_anthropic(prompt: str, model: str, timeout: int) -> Dict[str, Any]:
    try:
        import anthropic  # pip install anthropic
    except Exception as e:
        raise RuntimeError("Anthropic provider selected but 'anthropic' SDK not installed. pip install anthropic") from e
    import os
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY missing in environment.")
    client = anthropic.Client(api_key=api_key, timeout=timeout)
    # Claude messages call — adjust per latest SDK version
    msg = client.messages.create(
        model=model,
        max_tokens=256,
        system="Return JSON only.",
        messages=[{"role":"user","content":_prompt}],
    )
    text = msg.content[0].text if getattr(msg, "content", None) else "{}"
    try:
        data = json.loads(text)
        return {"score": float(data["score"]), "rationale": str(data["rationale"])}
    except Exception:
        return {"score": 0.5, "rationale": "Anthropic: parse fallback"}
    