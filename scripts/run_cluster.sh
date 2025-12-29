#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

source .venv/bin/activate

echo "Starting tiny-kv cluster..."
echo "Primary: 5001 | Replicas: 5002, 5003"

python -m tiny_kv.node --name node1 --role primary --port 5001 --peers "http://127.0.0.1:5002,http://127.0.0.1:5003" &
P1=$!

python -m tiny_kv.node --name node2 --role replica --port 5002 --sync-from "http://127.0.0.1:5001" &
P2=$!

python -m tiny_kv.node --name node3 --role replica --port 5003 --sync-from "http://127.0.0.1:5001" &
P3=$!

echo "PIDs: $P1 $P2 $P3"
echo "Press Ctrl+C to stop all."

trap "kill $P1 $P2 $P3 2>/dev/null || true" INT TERM
wait