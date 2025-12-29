from __future__ import annotations

import argparse

import requests

from .api import create_app
from .config import NodeConfig
from .store import KVStore


def parse_peers(raw: str) -> list[str]:
    raw = raw.strip()
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="tiny-kv node")
    parser.add_argument("--name", default="node")
    parser.add_argument("--role", choices=["primary", "replica"], default="replica")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument(
        "--peers",
        default="",
        help="Comma-separated base URLs, e.g. http://127.0.0.1:5002,http://127.0.0.1:5003",
    )
    parser.add_argument(
        "--sync-from",
        default="",
        help="Base URL to sync from on startup, e.g. http://127.0.0.1:5001",
    )
    args = parser.parse_args()

    cfg = NodeConfig(
        name=args.name,
        role=args.role,
        host=args.host,
        port=args.port,
        peers=parse_peers(args.peers),
    )

    store = KVStore()

    # Optional startup sync (for replicas that restart)
    if args.sync_from:
        try:
            snap = requests.get(f"{args.sync_from}/internal/sync", timeout=2.0).json()
            store.apply_state(snap)
            print(f"[{cfg.name}] synced from {args.sync_from}")
        except Exception as e:
            print(f"[{cfg.name}] sync failed: {e}")

    app = create_app(store, cfg)

    # debug=False avoids Flask reloader spawning extra PIDs (important for multi-node)
    app.run(host=cfg.host, port=cfg.port, debug=False)


if __name__ == "__main__":
    main()