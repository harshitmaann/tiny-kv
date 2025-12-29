from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import requests

from .config import NodeConfig


@dataclass(frozen=True)
class ReplicationResult:
    acks: int
    required: int
    errors: Dict[str, str]


def quorum_required(total_nodes: int) -> int:
    return (total_nodes // 2) + 1


def replicate_to_peers(
    cfg: NodeConfig,
    key: str,
    value: Optional[str],
    version: int,
    deleted: bool,
) -> ReplicationResult:
    """
    Send the write/delete to all peers. Primary counts as 1 ACK locally.
    Success ACK = peer returns HTTP 200.
    """
    total_nodes = 1 + len(cfg.peers)
    required = quorum_required(total_nodes)

    acks = 1  # local primary already applied
    errors: Dict[str, str] = {}

    payload = {"value": value, "version": version, "deleted": deleted}

    for peer in cfg.peers:
        url = f"{peer}/internal/replica/kv/{key}"
        try:
            r = requests.post(url, json=payload, timeout=cfg.timeout_s)
            if r.status_code == 200:
                acks += 1
            else:
                errors[peer] = f"HTTP {r.status_code}"
        except Exception as e:
            errors[peer] = str(e)

    return ReplicationResult(acks=acks, required=required, errors=errors)