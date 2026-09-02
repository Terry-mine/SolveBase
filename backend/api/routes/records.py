"""记录 CRUD 与检索。

P0 提供：列表过滤、关键词搜索、详情、新建、局部更新、软删。
P2 会在 search 接口里叠加指纹与向量召回 —— 路由签名不变，只换实现。
"""

from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ...db.repositories.jobs import VocabRepository
from ...db.repositories.records import RecordRepository
from ...domain.models import Page, RecordIn, RecordOut, RecordPatch
from ...domain.payloads import validate
from ...domain.vocab import get_vocabulary
from ..deps import assert_known_type, get_conn, get_repo

router = APIRouter(prefix="/records", tags=["records"])


def _normalize_incoming(data: dict[str, Any]) -> dict[str, Any]:
    """把自由输入的分类/状态收敛回词表 code。

    收敛不到就置空（不报错），由前端标为"待确认"。
    P1 接 LLM 后，这一步就是自动归并的核心。
    """
    vocab = get_vocabulary()
    record_type = data.get("record_type")
    if record_type:
        vocab.get(record_type)  # 未知类型直接 400

    if data.get("category"):
        data["category"] = vocab.normalize_category(record_type, data["category"])
    if data.get("status"):
        data["status"] = vocab.normalize_status(record_type, data["status"]) or data["status"]
    if record_type:
        data["payload"] = validate(record_type, data.get("payload"))
    return data


@router.get("", response_model=Page)
def list_records(
    record_type: str | None = None,
    category: str | None = None,
    project: str | None = None,
    status: str | None = None,
    system: str | None = None,
    tag: str | None = None,
    q: str | None = None,
    order: str = "updated",
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    repo: RecordRepository = Depends(get_repo),
) -> Page:
    items, total = repo.list(
        {
            "record_type": record_type, "category": category, "project": project,
            "status": status, "system": system, "tag": tag, "q": q,
            "order": order, "limit": limit, "offset": offset,
        }
    )
    return Page(
        items=[RecordOut.model_validate(i) for i in items],
        total=total, offset=offset, limit=limit,
    )


@router.get("/stats")
def stats(repo: RecordRepository = Depends(get_repo)) -> dict:
    return {
        "by_type": repo.count_by("record_type"),
        "by_category": repo.count_by("category"),
        "by_project": repo.count_by("project"),
        "by_status": repo.count_by("status"),
    }


@router.get("/search", response_model=Page)
def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    repo: RecordRepository = Depends(get_repo),
) -> Page:
    """关键词检索。

    P2 会升级为「指纹 + BM25 + 向量 → RRF → rerank」的混合检索，
    但对外仍是这个接口，前端不用改。
    """
    hits = repo.search_ids(q, limit=limit)
    items = []
    for record_id, score in hits:
        item = repo.get(record_id)
        if item:
            items.append(RecordOut.model_validate(item))
    return Page(items=items, total=len(items), offset=0, limit=limit)


@router.post("", response_model=RecordOut, status_code=201)
def create_record(
    payload: RecordIn,
    repo: RecordRepository = Depends(get_repo),
    conn: sqlite3.Connection = Depends(get_conn),
) -> RecordOut:
    assert_known_type(payload.record_type)
    data = _normalize_incoming(payload.model_dump())
    record_id = repo.create(data)

    if data.get("category"):
        VocabRepository(conn).bump_usage("category", data["record_type"], data["category"])

    created = repo.get(record_id)
    if created is None:  # pragma: no cover
        raise HTTPException(status_code=500, detail="创建后无法读回记录")
    return RecordOut.model_validate(created)


@router.get("/{record_id}", response_model=RecordOut)
def get_record(record_id: str, repo: RecordRepository = Depends(get_repo)) -> RecordOut:
    item = repo.get(record_id)
    if item is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    return RecordOut.model_validate(item)


@router.patch("/{record_id}", response_model=RecordOut)
def patch_record(
    record_id: str,
    payload: RecordPatch,
    repo: RecordRepository = Depends(get_repo),
) -> RecordOut:
    current = repo.get(record_id)
    if current is None:
        raise HTTPException(status_code=404, detail="记录不存在")

    patch = payload.model_dump(exclude_unset=True)
    record_type = patch.get("record_type") or current["record_type"]
    if "record_type" in patch:
        assert_known_type(record_type)
    patch["record_type"] = record_type

    updated = repo.update(record_id, _normalize_incoming(patch))
    if updated is None:  # pragma: no cover
        raise HTTPException(status_code=404, detail="记录不存在")
    return RecordOut.model_validate(updated)


@router.delete("/{record_id}")
def delete_record(record_id: str, repo: RecordRepository = Depends(get_repo)) -> dict:
    if not repo.soft_delete(record_id):
        raise HTTPException(status_code=404, detail="记录不存在或已删除")
    return {"id": record_id, "deleted": True}
