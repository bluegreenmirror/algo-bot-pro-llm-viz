"""Runtime helpers for trading mode and kill-switch (v1 safety contract)."""
from __future__ import annotations

import os
from typing import Literal
from urllib.parse import urlparse

Mode = Literal["mock", "paper", "live"]
VALID_MODES: tuple[Mode, ...] = ("mock", "paper", "live")

PAPER_HOST = "paper-api.alpaca.markets"
LIVE_HOST = "api.alpaca.markets"
DEFAULT_PAPER_URL = f"https://{PAPER_HOST}"


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


def require_endpoint_for_mode(mode: Mode, base_url: str | None = None) -> None:
    """
    Bind each broker mode to exactly one Alpaca host so that paper can never
    reach the live endpoint and live can never silently run against paper.
    """
    if mode == "mock":
        return
    url = base_url if base_url is not None else os.getenv("ALPACA_BASE_URL", DEFAULT_PAPER_URL)
    parsed = urlparse(url.strip())
    expected = PAPER_HOST if mode == "paper" else LIVE_HOST
    if parsed.scheme != "https" or (parsed.hostname or "").lower() != expected:
        raise RuntimeError(
            f"{mode} mode requires ALPACA_BASE_URL=https://{expected}; got {url!r}"
        )
