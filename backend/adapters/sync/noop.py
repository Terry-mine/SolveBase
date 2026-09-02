"""P0 占位：不同步。

接口和数据结构已经是最终形态（记录级 changeset + 冲突列表），
P4 实现 LocalBundleSync（导出/导入 zip）和 DriveSync（网盘目录）时，
直接照着这个接口填实现即可，数据模型不用改。
"""

from __future__ import annotations

from typing import Any

from ...ports.sync import ChangeSet, SyncResult
from ...services.registry import register


@register("sync", "noop")
class NoopSync:
    name = "noop"

    def __init__(self, settings=None, **kwargs) -> None:
        self.settings = settings

    def pull(self, since: int) -> ChangeSet:
        return ChangeSet(cursor=since)

    def push(self, changes: ChangeSet) -> SyncResult:
        return SyncResult(message="同步未启用（provider=noop）")

    def status(self) -> dict[str, Any]:
        return {"enabled": False, "provider": self.name, "note": "P4 阶段启用"}
