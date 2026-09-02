"""FastAPI 依赖注入。

这里是唯一把「配置 / 连接 / 仓储 / 服务」组装起来的地方。
业务服务本身不 import settings，方便测试和复用。
"""

from __future__ import annotations

import sqlite3
from typing import Iterator

from fastapi import Depends, HTTPException

from ..core.config import Settings, get_settings
from ..db.connection import connect
from ..db.repositories.jobs import JobRepository
from ..db.repositories.records import RecordRepository
from ..domain.vocab import UnknownRecordTypeError, get_vocabulary
from ..ports.sync import SyncProvider
from ..services.capture import CaptureDeps, CaptureService
from ..services.providers import get_providers


def get_conn() -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    settings.ensure_dirs()
    conn = connect(settings.database_path)
    try:
        yield conn
    finally:
        conn.close()


def get_repo(conn: sqlite3.Connection = Depends(get_conn)) -> RecordRepository:
    settings = get_settings()
    return RecordRepository(conn, device_id=settings.device_id, schema_ver=settings.schema_ver)


def get_jobs(conn: sqlite3.Connection = Depends(get_conn)) -> JobRepository:
    return JobRepository(conn)


def get_sync() -> SyncProvider:
    return get_providers().sync


def get_capture_service(
    conn: sqlite3.Connection = Depends(get_conn),
    records: RecordRepository = Depends(get_repo),
    jobs: JobRepository = Depends(get_jobs),
) -> CaptureService:
    return CaptureService(CaptureDeps(conn=conn, records=records, jobs=jobs, vocab=get_vocabulary()))


def assert_known_type(record_type: str) -> None:
    try:
        get_vocabulary().get(record_type)
    except UnknownRecordTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def current_settings() -> Settings:
    return get_settings()
