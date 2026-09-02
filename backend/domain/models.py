"""对外数据模型。

这些是 API 的输入输出契约。内部存储（records 表的列）不直接暴露，
中间隔一层 record_mapper，这样改表结构不会波及 API。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .enums import DRAFT_STATUS, RecordType


class AttemptIn(BaseModel):
    seq: int | None = None
    hypothesis: str | None = None
    action: str | None = None
    observation: str | None = None
    worked: int = 0
    elapsed_min: int | None = None


class AttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    seq: int
    hypothesis: str | None = None
    action: str | None = None
    observation: str | None = None
    worked: int = 0
    elapsed_min: int | None = None


class SnippetIn(BaseModel):
    kind: str | None = None
    lang: str | None = None
    body: str
    note: str | None = None


class SnippetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: str | None = None
    lang: str | None = None
    body: str
    note: str | None = None
    copy_count: int = 0


class RecordIn(BaseModel):
    """新建/更新记录的通用入参。

    payload 的合法键由 record_type 决定，校验在 domain/payloads.py，
    加一种新类型只需注册一个校验函数，不改这里。
    """

    record_type: str = RecordType.INCIDENT
    title: str
    status: str = DRAFT_STATUS
    category: str | None = None
    project: str | None = None
    systems: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    search_text: str | None = None
    error_excerpt: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    attempts: list[AttemptIn] = Field(default_factory=list)
    snippets: list[SnippetIn] = Field(default_factory=list)
    confidence: float | None = None
    missing: list[str] = Field(default_factory=list)


class RecordPatch(BaseModel):
    """局部更新。只传要改的字段，未传的保持原值。"""

    record_type: str | None = None
    title: str | None = None
    status: str | None = None
    category: str | None = None
    project: str | None = None
    systems: list[str] | None = None
    tags: list[str] | None = None
    search_text: str | None = None
    error_excerpt: str | None = None
    payload: dict[str, Any] | None = None
    attempts: list[AttemptIn] | None = None
    snippets: list[SnippetIn] | None = None
    confidence: float | None = None
    missing: list[str] | None = None


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    record_type: str
    title: str
    status: str
    category: str | None = None
    project: str | None = None
    systems: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    search_text: str = ""
    error_excerpt: str | None = None
    error_fp: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = None
    missing: list[str] = Field(default_factory=list)
    attempts: list[AttemptOut] = Field(default_factory=list)
    snippets: list[SnippetOut] = Field(default_factory=list)

    rev: int = 1
    device_id: str = ""
    dirty: int = 1
    schema_ver: int = 1
    hit_count: int = 0
    created_at: int = 0
    updated_at: int = 0
    deleted_at: int | None = None


class CaptureIn(BaseModel):
    """速记入口。字段越少越好 —— 输入摩擦决定这套系统能否活下去。"""

    text: str
    source: str = "web"
    record_type: str | None = None
    project: str | None = None


class CaptureOut(BaseModel):
    record_id: str
    job_id: str
    record_type: str
    title: str
    needs_review: bool


class Page(BaseModel):
    items: list[RecordOut]
    total: int
    offset: int
    limit: int
