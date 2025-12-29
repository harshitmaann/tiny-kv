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
        self._data: Dict[str, Record] = {}          # live records only
        self._tomb: Dict[str, int] = {}             # key -> deleted version

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
            # if a tombstone exists at lower version, keep it (harmless); if higher, put would have version > it anyway
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

    def upsert_if_newer(self, key: str, value: Optional[str], version: int, deleted: bool) -> Tuple[bool, Optional[Record]]:
        """
        Replica helper: apply incoming change only if version is newer than local knowledge.
        """
        with self._lock:
            known = self._max_known_version(key)
            if version <= known:
                return False, self._data.get(key)

            if deleted:
                self._data.pop(key, None)
                self._tomb[key] = version
                return True, None

            # normal write
            rec = Record(value=value, version=version, deleted=False)
            self._data[key] = rec
            return True, rec