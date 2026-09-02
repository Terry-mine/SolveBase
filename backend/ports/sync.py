"""同步端口。

P0 挂 NoopSync（什么都不做），但**接口和数据结构从第一版就定死**。
这样 P4 做同步时只是"填一个实现"，而不是回头改数据模型。

硬约束：同步单元是「记录级 changeset」，不是数据库文件。
把 .db 文件放进网盘同步会导致损坏。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class ChangeSet:
    """一次同步的增量。"""

    records: list[dict[str, Any]] = field(default_factory=list)
    deleted_ids: list[str] = field(default_factory=list)
    cursor: int = 0
    device_id: str = ""


@dataclass
class Conflict:
    record_id: str
    local_rev: int
    remote_rev: int
    reason: str


@dataclass
class SyncResult:
    pulled: int = 0
    pushed: int = 0
    conflicts: list[Conflict] = field(default_factory=list)
    message: str = ""


@runtime_checkable
class SyncProvider(Protocol):
    name: str

    def pull(self, since: int) -> ChangeSet:
        ...

    def push(self, changes: ChangeSet) -> SyncResult:
        ...

    def status(self) -> dict[str, Any]:
        ...
