import json
import uuid

import pytest

from app.core.cache import (
    get_cached_request,
    invalidate_request_cache,
    request_cache_index_key,
    request_cache_key,
    set_cached_request,
)


def test_user_scoped_cache_keys_differ():
    rid = uuid.uuid4()
    uid_a = uuid.uuid4()
    uid_b = uuid.uuid4()
    assert request_cache_key(rid, uid_a) != request_cache_key(rid, uid_b)


def test_invalidate_clears_indexed_keys(fake_redis):
    rid = uuid.uuid4()
    uid = uuid.uuid4()
    payload = {"id": str(rid), "title": "test"}

    set_cached_request(rid, uid, payload)
    key = request_cache_key(rid, uid)
    assert fake_redis.get(key) is not None
    assert fake_redis.smembers(request_cache_index_key(rid)) == {key}

    invalidate_request_cache(rid)
    assert fake_redis.get(key) is None
    assert fake_redis.smembers(request_cache_index_key(rid)) == set()


@pytest.mark.asyncio
async def test_get_request_idor_other_user_gets_404(require_db, client, two_users_with_request, fake_redis):
    sr = two_users_with_request["request"]
    token_a = two_users_with_request["token_a"]
    token_b = two_users_with_request["token_b"]

    res_a = await client.get(
        f"/requests/{sr.id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_a.status_code == 200

    legacy_key = f"request:{sr.id}"
    fake_redis.set(legacy_key, json.dumps(res_a.json()))

    res_b = await client.get(
        f"/requests/{sr.id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.status_code == 404


@pytest.mark.asyncio
async def test_cache_invalidated_after_cancel(require_db, client, two_users_with_request, fake_redis):
    sr = two_users_with_request["request"]
    token_a = two_users_with_request["token_a"]

    await client.get(f"/requests/{sr.id}", headers={"Authorization": f"Bearer {token_a}"})
    key = request_cache_key(sr.id, two_users_with_request["user_a"].id)
    assert fake_redis.get(key) is not None

    cancel = await client.patch(
        f"/requests/{sr.id}/cancel",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert cancel.status_code == 200
    assert fake_redis.get(key) is None
