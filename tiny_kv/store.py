from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class Record:
    value: Optional[str]
    version: int
    deleted: bool = False


class KVStore:
    """
    Thread-safe in-memory KV store with per-key versioning + tombstones.

    - put() increments version
    - delete() increments version and records a tombstone
    - replicas use upsert_if_newer() with (value, version, deleted)
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._data: Dict[str, Record] = {}  # live records only
        self._tomb: Dict[str, int] = {}     # key -> deleted version

    def _max_known_version(self, key: str) -> int:
        live_v = self._data[key].version if key in self._data else 0
        tomb_v = self._tomb.get(key, 0)
        return live_v if live_v >= tomb_v else tomb_v

    def get(self, key: str) -> Optional[Record]:
        with self._lock:
            return self._data.get(key)

    def put(self, key: str, value: str) -> Record:
        with self._lock:
            next_version = self._max_known_version(key) + 1
            rec = Record(value=value, version=next_version, deleted=False)
            self._data[key] = rec
            return rec

    def delete(self, key: str) -> Tuple[bool, int]:
        """
        Delete the key and record a tombstone version.
        Returns (existed, delete_version).
        """
        with self._lock:
            existed = key in self._data
            delete_version = self._max_known_version(key) + 1
            self._data.pop(key, None)
            self._tomb[key] = delete_version
            return existed, delete_version

    def upsert_if_newer(
        self, key: str, value: Optional[str], version: int, deleted: bool
    ) -> Tuple[bool, Optional[Record]]:
        """
        Replica helper: apply incoming change only if version is newer than local knowledge.
        Returns (applied, resulting_record_or_none).
        """
        with self._lock:
            known = self._max_known_version(key)
            if version <= known:
                return False, self._data.get(key)

            if deleted:
                self._data.pop(key, None)
                self._tomb[key] = version
                return True, None

            rec = Record(value=value, version=version, deleted=False)
            self._data[key] = rec
            return True, rec

    def dump_state(self) -> dict:
        """Return a JSON-serializable snapshot of live data + tombstones."""
        with self._lock:
            data = {
                k: {"value": v.value, "version": v.version}
                for k, v in self._data.items()
            }
            tomb = dict(self._tomb)
            return {"data": data, "tomb": tomb}

    def apply_state(self, snapshot: dict) -> None:
        """Merge a snapshot into local state using version rules."""
        data = snapshot.get("data", {}) or {}
        tomb = snapshot.get("tomb", {}) or {}

        with self._lock:
            # Apply tombstones first
            for k, v in tomb.items():
                if isinstance(v, int):
                    known = self._max_known_version(k)
                    if v > known:
                        self._data.pop(k, None)
                        self._tomb[k] = v

            # Apply live records
            for k, rec in data.items():
                if not isinstance(rec, dict):
                    continue
                value = rec.get("value")
                version = rec.get("version")
                if isinstance(value, str) and isinstance(version, int):
                    # Use replica rule so version comparisons stay correct
                    self.upsert_if_newer(k, value=value, version=version, deleted=False)