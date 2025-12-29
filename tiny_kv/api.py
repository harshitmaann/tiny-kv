from __future__ import annotations

from flask import Flask, jsonify, request

from .store import KVStore


def create_app(store: KVStore) -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"ok": True})

    @app.get("/kv/<key>")
    def get_key(key: str):
        rec = store.get(key)
        if rec is None:
            return jsonify({"error": "not_found"}), 404
        return jsonify({"key": key, "value": rec.value, "version": rec.version})

    @app.put("/kv/<key>")
    def put_key(key: str):
        body = request.get_json(silent=True) or {}
        value = body.get("value")
        if value is None or not isinstance(value, str):
            return jsonify({"error": "value_required", "hint": "JSON body like {'value': '...'}"}), 400

        rec = store.put(key, value)
        return jsonify({"key": key, "value": rec.value, "version": rec.version})

    @app.delete("/kv/<key>")
    def delete_key(key: str):
        existed = store.delete(key)
        if not existed:
            return jsonify({"error": "not_found"}), 404
        return jsonify({"key": key, "deleted": True})

    # Internal endpoint for replication (we'll use this in Step 3)
    @app.post("/internal/replica/kv/<key>")
    def replica_upsert(key: str):
        body = request.get_json(silent=True) or {}
        value = body.get("value")
        version = body.get("version")

        if not isinstance(value, str) or not isinstance(version, int):
            return jsonify({"error": "value_and_version_required"}), 400

        applied, rec = store.upsert_if_newer(key, value, version)
        return jsonify(
            {
                "key": key,
                "applied": applied,
                "value": rec.value if rec else None,
                "version": rec.version if rec else None,
            }
        )

    return app