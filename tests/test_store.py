from tiny_kv.store import KVStore


def test_put_get_version_increments():
    s = KVStore()
    r1 = s.put("a", "one")
    assert r1.version == 1
    r2 = s.put("a", "two")
    assert r2.version == 2
    got = s.get("a")
    assert got is not None
    assert got.value == "two"
    assert got.version == 2


def test_delete_creates_tombstone_and_blocks_old_writes():
    s = KVStore()
    s.put("k", "v1")
    existed, del_v = s.delete("k")
    assert existed is True
    assert s.get("k") is None

    # older version should not resurrect
    applied, _ = s.upsert_if_newer("k", value="old", version=1, deleted=False)
    assert applied is False

    # newer write should be accepted
    applied, rec = s.upsert_if_newer("k", value="new", version=del_v + 1, deleted=False)
    assert applied is True
    assert rec is not None
    assert rec.value == "new"