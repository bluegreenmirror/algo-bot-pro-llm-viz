"""Runtime helpers for trading mode and kill-switch (v1 safety contract)."""
from __future__ import annotations

import os
from typing import Literal

Mode = Literal["mock", "paper", "live"]
VALID_MODES: tuple[Mode, ...] = ("mock", "paper", "live")


def is_trading_enabled() -> bool:
    """Broker submits are allowed only when ENABLE_TRADING is exactly true."""
    return os.getenv("ENABLE_TRADING", "").strip().lower() == "true"


def resolve_mode(mode: str | None = None, *, mock: bool = False, live: bool = False) -> Mode:
    """
    Resolve mock|paper|live.

    Compatibility: --mock => mock, --live => paper (legacy flag meant Alpaca paper).
    Explicit --mode wins when provided.
    """
    if mode:
        normalized = mode.strip().lower()
        if normalized not in VALID_MODES:
            raise ValueError(f"mode must be one of {', '.join(VALID_MODES)}; got {mode!r}")
        if mock or live:
            raise ValueError("Use either --mode or --mock/--live, not both")
        return normalized  # type: ignore[return-value]
    if mock and live:
        raise ValueError("Cannot combine --mock and --live")
    if mock:
        return "mock"
    if live:
        return "paper"
    return "mock"


def require_alpaca_keys() -> None:
    if not os.getenv("ALPACA_KEY_ID") or not os.getenv("ALPACA_SECRET_KEY"):
        raise RuntimeError(
            "paper/live mode requires ALPACA_KEY_ID and ALPACA_SECRET_KEY. "
            "Use --mode mock or set keys in .env."
        )
