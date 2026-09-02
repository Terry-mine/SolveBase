"""同步状态。

P0 阶段 provider 是 noop，这里返回"未启用"。
P4 实现 LocalBundleSync / DriveSync 后，接口形状完全不用变。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ...ports.sync import SyncProvider
from ..deps import get_sync

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status")
def status(provider: SyncProvider = Depends(get_sync)) -> dict:
    return {"provider": provider.name, **provider.status()}
