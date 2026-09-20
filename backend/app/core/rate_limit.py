from __future__ import annotations

from datetime import UTC, datetime

from redis import Redis


class QuotaExceeded(RuntimeError):
    def __init__(self, reset_at: datetime) -> None:
        self.reset_at = reset_at
        super().__init__("hosted quota exhausted")


class RedisQuotaLimiter:
    def __init__(self, redis: Redis, limit: int, window_seconds: int) -> None:
        self.redis = redis
        self.limit = limit
        self.window_seconds = window_seconds

    def _key(self, identifier: str) -> str:
        window = int(datetime.now(UTC).timestamp()) // self.window_seconds
        return f"quota:{window}:{identifier}"

    def _reset_at(self) -> datetime:
        now = int(datetime.now(UTC).timestamp())
        reset = ((now // self.window_seconds) + 1) * self.window_seconds
        return datetime.fromtimestamp(reset, tz=UTC)

    def consume(self, identifier: str) -> int:
        key = self._key(identifier)
        with self.redis.pipeline() as pipe:
            pipe.incr(key)
            pipe.expire(key, self.window_seconds)
            count, _ = pipe.execute()
        if int(count) > self.limit:
            raise QuotaExceeded(self._reset_at())
        return max(0, self.limit - int(count))

    def remaining(self, identifier: str) -> int:
        count = self.redis.get(self._key(identifier))
        if count is None:
            return self.limit
        return max(0, self.limit - int(count))

    def reset_at(self) -> datetime:
        return self._reset_at()
