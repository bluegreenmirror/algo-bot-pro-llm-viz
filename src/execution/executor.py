from __future__ import annotations
from typing import Callable, Dict, Any, List
from datetime import datetime
from src.strategy.sma import sma_signal, score_from_signal, blend_scores
from src.policy.engine import PolicyEngine
from src.compliance.engine import ComplianceEngine
from src.audit.logger import write_audit
from src.risk.portfolio import PortfolioLimits, can_open_positions
from src.agent.llm import score as llm_score
from src.config import Settings

def run_daily(
    universe: List[str],
    bars_dict: Dict[str, List[float]],
    *,
    fast: int,
    slow: int,
    risk_per_trade: float,
    stop_loss_pct: float,
    take_profit_pct: float,
    max_positions: int,
    submit_fn: Callable[..., Dict[str, Any]] | None
) -> Dict[str, Any]:
    settings = Settings()
    equity = 100000.0  # replace with portfolio equity if you add state

    # Score per symbol (SMA + optional LLM)
    scored = []
    for sym in universe:
        closes = bars_dict.get(sym, [])
        if not closes: continue
        sig = sma_signal(closes, fast=fast, slow=slow)
        sma_sc = score_from_signal(sig)
        features = {"fast": fast, "slow": slow, "last": closes[-1], "n": len(closes)}
        llm = llm_score(sym, features)
        final = blend_scores(sma_sc, llm.score, w=settings.llm_weight)
        scored.append({"symbol": sym, "score": final, "sma": sma_sc, "llm": llm.score, "rationale": llm.rationale})
        write_audit({"event":"score","symbol":sym,"sma_score":sma_sc,"llm_score":llm.score,"final":final,"rationale":llm.rationale})

    selected = sorted(scored, key=lambda x: x["score"], reverse=True)[:max_positions]

    # Exposure cap
    per_trade = equity * risk_per_trade / max(1e-9, stop_loss_pct)
    allowed = can_open_positions(equity, per_trade, len(selected), PortfolioLimits(max_total_exposure_pct=0.5))
    selected = selected[:allowed]

    results = {}
    for sc in selected:
        sym = sc["symbol"]
        closes = bars_dict[sym]
        last_price = closes[-1]
        pol = PolicyEngine().check_all(notional=min(per_trade, equity))
        comp = ComplianceEngine().check_all(symbol=sym, now=datetime.now())
        decision = {"symbol": sym, "score": sc["score"], "last": last_price, "policy_ok": pol.ok, "compliance_ok": comp.ok}
        if pol.ok and comp.ok and submit_fn:
            side = "buy" if sma_signal(closes, fast=fast, slow=slow) == "buy" else "sell"
            order = submit_fn(sym, notional=per_trade, side=side)
            decision["order"] = {"id": getattr(order,"id","ord_mock"), "status": getattr(order,"status","accepted")}
            decision["action"] = "placed"
        else:
            decision["action"] = "blocked"
        results[sym] = decision
        write_audit({"event":"decision", **decision})
    return {"equity": equity, "selected": [s["symbol"] for s in selected], "results": results}
