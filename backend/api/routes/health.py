"""健康检查。

一眼看清：库在哪、迁移到哪一版、挂了哪些 provider。
排查问题时第一个该看的接口。
"""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ...core.config import Settings
from ...db.migrations.runner import applied_versions
from ...domain.vocab import get_vocabulary
from ..deps import current_settings, get_conn
from ...services.providers import capabilities

router = APIRouter(tags=["system"])


@router.get("/health")
def health(
    conn: sqlite3.Connection = Depends(get_conn),
    settings: Settings = Depends(current_settings),
) -> dict:
    versions = applied_versions(conn)
    vocab = get_vocabulary()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "device_id": settings.device_id,
        "database": str(settings.database_path),
        "migrations": {"applied": versions, "latest": max(versions) if versions else 0},
        "vocab": {"version": vocab.version, "types": list(vocab.type_keys)},
        "providers": capabilities(),
    }
