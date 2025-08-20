from __future__ import annotations
from dataclasses import dataclass
from src.config import Settings

@dataclass
class PolicyResult:
    ok: bool
    reason: str = "ok"

class PolicyEngine:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def check_max_notional(self, notional: float) -> PolicyResult:
        if notional > self.settings.max_notional:
            return PolicyResult(False, f"notional>{self.settings.max_notional}")
        return PolicyResult(True, "ok")

    def check_all(self, *, notional: float) -> PolicyResult:
        return self.check_max_notional(notional)
