"""速记捕获服务。

P0 的链路：原文落 job（永久留痕）→ 建一条 draft 记录 → 可搜可编辑。
P1 在中间插一步 LLM 规整，其余不变。
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from ..db.repositories.jobs import JobRepository
from ..db.repositories.records import RecordRepository
from ..domain.enums import DRAFT_STATUS, JobStage
from ..domain.models import CaptureIn, CaptureOut
from ..domain.payloads import validate
from ..domain.vocab import Vocabulary
from .classify import extract_error_excerpt, guess_record_type, guess_title


@dataclass
class CaptureDeps:
    conn: sqlite3.Connection
    records: RecordRepository
    jobs: JobRepository
    vocab: Vocabulary


class CaptureService:
    def __init__(self, deps: CaptureDeps) -> None:
        self.deps = deps

    def capture(self, payload: CaptureIn) -> CaptureOut:
        record_type = payload.record_type or guess_record_type(payload.text)
        # 未知类型原样放行，由 payload 校验器兜底，不让录入流程崩掉
        self.deps.vocab.get(record_type)

        # title 硬性必填。前端已拦一道，这里再拦一次 —— 否则 curl 或
        # 其他入口能绕过去，库里又会堆满认不出来的「自动标题」。
        title = (payload.title or "").strip()
        if not title:
            raise ValueError("title 必填：先用一句话说清这是什么问题")

        data = {
            "record_type": record_type,
            "title": title,
            "status": DRAFT_STATUS,
            "project": payload.project,
            "search_text": payload.text,
            "error_excerpt": extract_error_excerpt(payload.text),
            "payload": validate(
                record_type,
                {"images": [img.model_dump() for img in payload.images]},
            ),
            "missing": ["category", "status", "attempts"],
        }

        record_id = self.deps.records.create(data)
        job_id = self.deps.jobs.create(payload.text, payload.source, record_id=record_id)
        self.deps.jobs.advance(job_id, JobStage.RAW, result={"record_id": record_id})

        return CaptureOut(
            record_id=record_id,
            job_id=job_id,
            record_type=record_type,
            title=title,
            needs_review=True,
        )
