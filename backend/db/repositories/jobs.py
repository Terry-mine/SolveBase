"""ingest_jobs / corrections 的数据访问层。"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from ...core.ids import new_id, now_ms
from ...domain.enums import JobStage


class JobRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, raw_text: str, source: str, record_id: str | None = None) -> str:
        jid = new_id()
        ts = now_ms()
        with self.conn:
            self.conn.execute(
                "INSERT INTO ingest_jobs (id, record_id, raw_text, source, stage, created_at, updated_at)"
                " VALUES (?,?,?,?,?,?,?)",
                (jid, record_id, raw_text, source, JobStage.RAW, ts, ts),
            )
        return jid

    def advance(self, job_id: str, stage: JobStage, result: dict[str, Any] | None = None,
                error: str | None = None) -> None:
        with self.conn:
            self.conn.execute(
                "UPDATE ingest_jobs SET stage = ?, result_json = ?, error = ?, updated_at = ? WHERE id = ?",
                (str(stage), json.dumps(result or {}, ensure_ascii=False), error, now_ms(), job_id),
            )

    def pending(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM ingest_jobs WHERE stage IN ('raw','failed') ORDER BY created_at LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class CorrectionRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def add(self, record_id: str, field: str, llm_value: str | None, human_value: str | None) -> str:
        cid = new_id()
        with self.conn:
            self.conn.execute(
                "INSERT INTO corrections (id, record_id, field, llm_value, human_value, created_at)"
                " VALUES (?,?,?,?,?,?)",
                (cid, record_id, field, llm_value, human_value, now_ms()),
            )
        return cid

    def recent(self, field: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        if field:
            rows = self.conn.execute(
                "SELECT * FROM corrections WHERE field = ? ORDER BY created_at DESC LIMIT ?",
                (field, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM corrections ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]


class VocabRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def replace_all(self, rows: list[dict[str, Any]]) -> int:
        with self.conn:
            self.conn.execute("DELETE FROM vocab")
            for r in rows:
                self.conn.execute(
                    "INSERT OR REPLACE INTO vocab "
                    "(kind, type_key, code, label, aliases_json, deprecated) VALUES (?,?,?,?,?,?)",
                    (
                        r["kind"], r["type_key"], r["code"], r["label"],
                        json.dumps(r["aliases"], ensure_ascii=False), r["deprecated"],
                    ),
                )
        return len(rows)

    def bump_usage(self, kind: str, type_key: str, code: str) -> None:
        with self.conn:
            self.conn.execute(
                "UPDATE vocab SET use_count = use_count + 1 "
                "WHERE kind = ? AND type_key = ? AND code = ?",
                (kind, type_key, code),
            )
