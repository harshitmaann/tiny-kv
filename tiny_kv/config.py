from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class NodeConfig:
    name: str
    role: str  # "primary" or "replica"
    host: str
    port: int
    peers: List[str]  # list of base URLs like ["http://127.0.0.1:5002", ...]
    timeout_s: float = 0.8