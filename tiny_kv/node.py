from __future__ import annotations

import argparse

from .api import create_app
from .store import KVStore


def main() -> None:
    parser = argparse.ArgumentParser(description="tiny-kv node")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()

    store = KVStore()
    app = create_app(store)
    app.run(host=args.host, port=args.port, debug=True)


if __name__ == "__main__":
    main()