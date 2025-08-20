from __future__ import annotations
import json, os, time
from typing import Any, Dict

def write_audit(event: Dict[str, Any], path: str = "logs/audit.jsonl") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    evt = {"ts": int(time.time()), **event}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(evt) + "\n")
