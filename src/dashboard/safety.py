"""Guards for the Streamlit dashboard, kept free of Streamlit for testing."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

BACKTEST_DIR = "logs"


def broker_modes_allowed() -> bool:
    """The dashboard has no auth, so paper/live runs need an explicit opt-in."""
    return os.getenv("DASHBOARD_ALLOW_BROKER", "").strip().lower() == "true"


def allowed_modes() -> List[str]:
    return ["mock", "paper", "live"] if broker_modes_allowed() else ["mock"]


def resolve_backtest_path(user_path: str, base_dir: str = BACKTEST_DIR) -> Path:
    """
    Resolve a user-supplied backtest path, refusing anything outside base_dir
    or not ending in .jsonl so the dashboard cannot read arbitrary files.
    """
    base = Path(base_dir).resolve()
    candidate = Path(user_path)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    resolved = candidate.resolve()
    if not resolved.is_relative_to(base):
        raise ValueError(f"backtest path must be inside {base_dir}/")
    if resolved.suffix != ".jsonl":
        raise ValueError("backtest path must be a .jsonl file")
    return resolved
