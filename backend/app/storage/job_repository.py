from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

from redis import Redis
from redis.exceptions import WatchError

from backend.app.domain.document import CanonicalDocument
from backend.app.domain.jobs import JobRecord


class JobRepositoryProblem(RuntimeError):
    pass


class DuplicateJob(JobRepositoryProblem):
    pass


class JobNotFound(JobRepositoryProblem):
    pass


class RevisionConflict(JobRepositoryProblem):
    pass


class JobRepository:
    def __init__(self, redis: Redis, ttl_seconds: int = 3600) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def _key(job_id: str) -> str:
        return f"job:{job_id}"

    @classmethod
    def _document_key(cls, job_id: str) -> str:
        return f"{cls._key(job_id)}:document"

    @classmethod
    def _events_key(cls, job_id: str) -> str:
        return f"{cls._key(job_id)}:events"

    @classmethod
    def _channel(cls, job_id: str) -> str:
        return f"{cls._key(job_id)}:progress"

    @staticmethod
    def _text(value: str | bytes) -> str:
        return value.decode() if isinstance(value, bytes) else value

    def create(self, record: JobRecord) -> None:
        key = self._key(record.id)
        created = self.redis.set(
            key,
            record.model_dump_json(),
            nx=True,
            ex=self.ttl_seconds,
        )
        if not created:
            raise DuplicateJob(record.id)
        self._publish(record)

    def get(self, job_id: str) -> JobRecord | None:
        raw = self.redis.get(self._key(job_id))
        if raw is None:
            return None
        return JobRecord.model_validate_json(self._text(raw))

    def update(
        self,
        job_id: str,
        expected_revision: int,
        changes: Mapping[str, Any],
    ) -> JobRecord:
        forbidden = {"id", "revision", "created_at"}
        if forbidden.intersection(changes):
            raise ValueError("job identity and revision fields cannot be changed")
        key = self._key(job_id)
        with self.redis.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(key)  # type: ignore[no-untyped-call]
                    raw = pipe.get(key)
                    if raw is None:
                        pipe.unwatch()
                        raise JobNotFound(job_id)
                    current = JobRecord.model_validate_json(self._text(raw))
                    if current.revision != expected_revision:
                        pipe.unwatch()
                        raise RevisionConflict(job_id)
                    now = datetime.now(UTC)
                    updated = current.model_copy(
                        update={
                            **dict(changes),
                            "revision": current.revision + 1,
                            "expires_at": now + timedelta(seconds=self.ttl_seconds),
                        }
                    )
                    updated = JobRecord.model_validate(updated)
                    payload = updated.model_dump_json()
                    pipe.multi()
                    pipe.set(key, payload, ex=self.ttl_seconds)
                    pipe.publish(self._channel(job_id), payload)
                    pipe.rpush(self._events_key(job_id), payload)
                    pipe.expire(self._events_key(job_id), self.ttl_seconds)
                    pipe.execute()
                    return updated
                except WatchError:
                    continue

    def save_document(self, document: CanonicalDocument) -> None:
        if self.get(document.job_id) is None:
            raise JobNotFound(document.job_id)
        with self.redis.pipeline() as pipe:
            pipe.set(
                self._document_key(document.job_id),
                document.model_dump_json(),
                ex=self.ttl_seconds,
            )
            pipe.expire(self._key(document.job_id), self.ttl_seconds)
            pipe.execute()

    def update_document(
        self,
        document: CanonicalDocument,
        expected_revision: int,
        changes: Mapping[str, Any] | None = None,
    ) -> JobRecord:
        key = self._key(document.job_id)
        with self.redis.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(key)  # type: ignore[no-untyped-call]
                    raw = pipe.get(key)
                    if raw is None:
                        pipe.unwatch()
                        raise JobNotFound(document.job_id)
                    current = JobRecord.model_validate_json(self._text(raw))
                    if current.revision != expected_revision:
                        pipe.unwatch()
                        raise RevisionConflict(document.job_id)
                    now = datetime.now(UTC)
                    updated = JobRecord.model_validate(
                        current.model_copy(
                            update={
                                **dict(changes or {}),
                                "revision": current.revision + 1,
                                "expires_at": now + timedelta(seconds=self.ttl_seconds),
                            }
                        )
                    )
                    record_payload = updated.model_dump_json()
                    pipe.multi()
                    pipe.set(key, record_payload, ex=self.ttl_seconds)
                    pipe.set(
                        self._document_key(document.job_id),
                        document.model_dump_json(),
                        ex=self.ttl_seconds,
                    )
                    pipe.publish(self._channel(document.job_id), record_payload)
                    pipe.rpush(self._events_key(document.job_id), record_payload)
                    pipe.expire(self._events_key(document.job_id), self.ttl_seconds)
                    pipe.execute()
                    return updated
                except WatchError:
                    continue

    def get_document(self, job_id: str) -> CanonicalDocument | None:
        raw = self.redis.get(self._document_key(job_id))
        if raw is None:
            return None
        return CanonicalDocument.model_validate_json(self._text(raw))

    def get_events(self, job_id: str) -> list[JobRecord]:
        values = self.redis.lrange(self._events_key(job_id), 0, -1)
        return [
            JobRecord.model_validate_json(self._text(value))
            for value in values
        ]

    def _publish(self, record: JobRecord) -> None:
        payload = record.model_dump_json()
        self.redis.publish(self._channel(record.id), payload)
        self.redis.rpush(self._events_key(record.id), payload)
        self.redis.expire(self._events_key(record.id), self.ttl_seconds)

    def delete(self, job_id: str) -> None:
        self.redis.delete(
            self._key(job_id),
            self._document_key(job_id),
            self._events_key(job_id),
        )
