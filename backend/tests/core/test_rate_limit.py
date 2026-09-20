import fakeredis
import pytest

from backend.app.core.rate_limit import QuotaExceeded, RedisQuotaLimiter


def test_quota_consumption_is_bounded_and_exposes_remaining() -> None:
    redis = fakeredis.FakeRedis(decode_responses=True)
    limiter = RedisQuotaLimiter(redis, limit=2, window_seconds=60)

    assert limiter.consume("127.0.0.1") == 1
    assert limiter.remaining("127.0.0.1") == 1
    assert limiter.consume("127.0.0.1") == 0
    with pytest.raises(QuotaExceeded):
        limiter.consume("127.0.0.1")


def test_quota_keys_are_scoped_and_expiring() -> None:
    redis = fakeredis.FakeRedis(decode_responses=True)
    limiter = RedisQuotaLimiter(redis, limit=1, window_seconds=60)

    limiter.consume("one")
    limiter.consume("two")

    assert redis.dbsize() == 2
    assert all(redis.ttl(key) > 0 for key in redis.scan_iter("quota:*"))
