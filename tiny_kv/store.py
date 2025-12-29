from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class Record:
    value: str
    version: int


class KVStore:
    """Thread-safe in-memory KV store with per-key versioning."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._data: Dict[str, Record] = {}

    def get(self, key: str) -> Optional[Record]:
        with self._lock:
            return self._data.get(key)

    def put(self, key: str, value: str) -> Record:
        with self._lock:
            current = self._data.get(key)
            next_version = 1 if current is None else current.version + 1
            rec = Record(value=value, version=next_version)
            self._data[key] = rec
            return rec

    def delete(self, key: str) -> bool:
        with self._lock:
            existed = key in self._data
            self._data.pop(key, None)
            return existed

    def upsert_if_newer(self, key: str, value: str, version: int) -> Tuple[bool, Optional[Record]]:
        """Replica helper: apply write only if incoming version is newer."""
        with self._lock:
            current = self._data.get(key)
            if current is None or version > current.version:
                rec = Record(value=value, version=version)
                self._data[key] = rec
                return True, rec
            return False, current