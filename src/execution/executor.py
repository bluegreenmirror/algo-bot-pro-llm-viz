from __future__ import annotations
from typing import Callable, Dict, Any, List
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
    submit_fn: Callable[..., Any] | None,
) -> Dict[str, Any]:
    settings = Settings()
    equity = 100000.0  # replace with portfolio equity if you add state

    # Score per symbol (SMA + optional LLM)
    scored = []
    for sym in universe:
        closes = bars_dict.get(sym, [])
        if not closes:
            continue
        sig = sma_signal(closes, fast=fast, slow=slow)
        sma_sc = score_from_signal(sig)
        features = {"fast": fast, "slow": slow, "last": closes[-1], "n": len(closes)}
        llm = llm_score(sym, features)
        final = blend_scores(sma_sc, llm.score, w=settings.llm_weight)
        scored.append({
            "symbol": sym,
            "signal": sig,
            "score": final,
            "sma": sma_sc,
            "llm": llm.score,
            "rationale": llm.rationale,
        })
        write_audit({
            "event": "score",
            "symbol": sym,
            "sma_score": sma_sc,
            "llm_score": llm.score,
            "final": final,
            "rationale": llm.rationale,
        })

    selected = sorted(scored, key=lambda x: x["score"], reverse=True)[:max_positions]

    # Exposure cap
    per_trade = equity * risk_per_trade / max(1e-9, stop_loss_pct)
    allowed = can_open_positions(
        equity, per_trade, len(selected), PortfolioLimits(max_total_exposure_pct=0.5)
    )
    selected = selected[:allowed]

    results = {}
    for sc in selected:
        sym = sc["symbol"]
        closes = bars_dict[sym]
        last_price = closes[-1]
        pol = PolicyEngine().check_all(notional=min(per_trade, equity))
        comp = ComplianceEngine().check_all(symbol=sym)
        decision = {
            "symbol": sym,
            "signal": sc["signal"],
            "score": sc["score"],
            "last": last_price,
            "policy_ok": pol.ok,
            "policy_reason": pol.reason,
            "compliance_ok": comp.ok,
            "compliance_reason": comp.reason,
        }
        # Long-only until positions are persisted (v1.1): a sell without a
        # tracked position would open a short, so only buy signals submit.
        if sc["signal"] != "buy":
            decision["action"] = "skipped"
            decision["block_reason"] = f"signal {sc['signal']}; long-only entries"
        elif pol.ok and comp.ok and submit_fn:
            order = submit_fn(
                sym,
                notional=per_trade,
                side="buy",
                take_profit_pct=take_profit_pct,
                stop_loss_pct=stop_loss_pct,
                ref_price=last_price,
            )
            decision["order"] = {
                "id": getattr(order, "id", None) or (order.get("id") if isinstance(order, dict) else "ord_mock"),
                "status": getattr(order, "status", None) or (order.get("status") if isinstance(order, dict) else "accepted"),
            }
            decision["action"] = "placed"
        else:
            decision["action"] = "blocked"
            if submit_fn is None:
                decision["block_reason"] = "trading disabled or no submit function"
            elif not pol.ok:
                decision["block_reason"] = pol.reason
            else:
                decision["block_reason"] = comp.reason
        results[sym] = decision
        write_audit({"event": "decision", **decision})
    return {"equity": equity, "selected": [s["symbol"] for s in selected], "results": results}
