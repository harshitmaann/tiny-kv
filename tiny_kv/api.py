from __future__ import annotations

from flask import Flask, jsonify, request

from .config import NodeConfig
from .replication import replicate_to_peers
from .store import KVStore


def create_app(store: KVStore, cfg: NodeConfig) -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "name": cfg.name, "role": cfg.role})

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

        # Replicas accept only internal replication writes
        if cfg.role != "primary":
            return jsonify({"error": "read_only_replica", "hint": "send writes to primary"}), 403

        rec = store.put(key, value)

        rep = replicate_to_peers(cfg, key=key, value=rec.value, version=rec.version, deleted=False)
        if rep.acks < rep.required:
            # In real systems you might roll back, but for learning we surface the failure.
            return jsonify({"error": "quorum_failed", "acks": rep.acks, "required": rep.required, "peer_errors": rep.errors}), 503

        return jsonify({"key": key, "value": rec.value, "version": rec.version, "acks": rep.acks, "required": rep.required})

    @app.delete("/kv/<key>")
    def delete_key(key: str):
        if cfg.role != "primary":
            return jsonify({"error": "read_only_replica", "hint": "send deletes to primary"}), 403

        existed, del_version = store.delete(key)

        rep = replicate_to_peers(cfg, key=key, value=None, version=del_version, deleted=True)
        if rep.acks < rep.required:
            return jsonify({"error": "quorum_failed", "acks": rep.acks, "required": rep.required, "peer_errors": rep.errors}), 503

        if not existed:
            # still returns 200 because delete is now replicated and versioned
            return jsonify({"key": key, "deleted": True, "existed": False, "version": del_version, "acks": rep.acks, "required": rep.required})

        return jsonify({"key": key, "deleted": True, "existed": True, "version": del_version, "acks": rep.acks, "required": rep.required})

    # Internal endpoint used by primary to replicate writes/deletes to replicas
    @app.post("/internal/replica/kv/<key>")
    def replica_apply(key: str):
        body = request.get_json(silent=True) or {}
        value = body.get("value")
        version = body.get("version")
        deleted = body.get("deleted")

        if not isinstance(version, int) or not isinstance(deleted, bool):
            return jsonify({"error": "version_and_deleted_required"}), 400

        if (value is not None) and (not isinstance(value, str)):
            return jsonify({"error": "value_must_be_string_or_null"}), 400

        applied, rec = store.upsert_if_newer(key, value=value, version=version, deleted=deleted)
        return jsonify(
            {
                "key": key,
                "applied": applied,
                "deleted": deleted,
                "value": rec.value if rec else None,
                "version": rec.version if rec else version,
            }
        )

    return app