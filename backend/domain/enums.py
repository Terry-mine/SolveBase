"""类型标识。

刻意做成"薄"的一层：记录类型、状态、分类的具体取值全部来自
config/vocab.yaml，这里只放最稳定的常量。

加一种记录类型时：往 vocab.yaml 加一项即可，本文件通常不用动。
"""

from __future__ import annotations

from enum import StrEnum


class RecordType(StrEnum):
    """内置记录类型。取值与 vocab.yaml 的 types 键保持一致。"""

    INCIDENT = "incident"
    RUNBOOK = "runbook"
    NOTE = "note"


class JobStage(StrEnum):
    RAW = "raw"
    NORMALIZED = "normalized"
    ENRICHED = "enriched"
    LINKED = "linked"
    DONE = "done"
    FAILED = "failed"


DRAFT_STATUS = "draft"


class Worked(StrEnum):
    """尝试链的结论。"""

    WORSE = "-1"
    FAILED = "0"
    WORKED = "1"

    @classmethod
    def coerce(cls, value) -> int:
        try:
            v = int(value)
        except (TypeError, ValueError):
            return 0
        return v if v in (-1, 0, 1) else 0
