"""records 的数据访问层。

约定：所有 SQL 只出现在这一层。业务服务只调用这里的方法，
因此将来换存储（比如迁到 Postgres）时，改动被限制在本文件内。
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Iterable

from ...core.ids import new_id, now_ms
from ...domain.enums import Worked

_LIST_COLUMNS = """
    id, record_type, title, status, category, project,
    systems_json, tags_json, search_text, error_excerpt, error_fp,
    payload_json, confidence, missing_json,
    rev, device_id, dirty, schema_ver, hit_count,
    created_at, updated_at, deleted_at
"""


def _load_json(raw: Any, default: Any) -> Any:
    if raw is None:
        return default
    if isinstance(raw, (list, dict)):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return default


def _dump_json(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False)


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "record_type": row["record_type"],
        "title": row["title"],
        "status": row["status"],
        "category": row["category"],
        "project": row["project"],
        "systems": _load_json(row["systems_json"], []),
        "tags": _load_json(row["tags_json"], []),
        "search_text": row["search_text"] or "",
        "error_excerpt": row["error_excerpt"],
        "error_fp": row["error_fp"],
        "payload": _load_json(row["payload_json"], {}),
        "confidence": row["confidence"],
        "missing": _load_json(row["missing_json"], []),
        "rev": row["rev"],
        "device_id": row["device_id"],
        "dirty": row["dirty"],
        "schema_ver": row["schema_ver"],
        "hit_count": row["hit_count"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "deleted_at": row["deleted_at"],
    }


class RecordRepository:
    def __init__(self, conn: sqlite3.Connection, *, device_id: str, schema_ver: int = 1) -> None:
        self.conn = conn
        self.device_id = device_id
        self.schema_ver = schema_ver

    # ── 写 ───────────────────────────────────────────────────────

    def create(self, data: dict[str, Any]) -> str:
        rid = data.get("id") or new_id()
        ts = now_ms()
        attempts = data.get("attempts") or []
        snippets = data.get("snippets") or []

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO records (
                    id, record_type, title, status, category, project,
                    systems_json, tags_json, search_text, error_excerpt, error_fp,
                    payload_json, confidence, missing_json,
                    rev, device_id, dirty, schema_ver, hit_count, created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,1,?,0,?,?)
                """,
                (
                    rid,
                    data["record_type"],
                    data["title"],
                    data.get("status", "draft"),
                    data.get("category"),
                    data.get("project"),
                    _dump_json(data.get("systems") or []),
                    _dump_json(data.get("tags") or []),
                    data.get("search_text") or "",
                    data.get("error_excerpt"),
                    data.get("error_fp"),
                    json.dumps(data.get("payload") or {}, ensure_ascii=False),
                    data.get("confidence"),
                    _dump_json(data.get("missing") or []),
                    self.device_id,
                    self.schema_ver,
                    ts,
                    ts,
                ),
            )
            self._replace_attempts(rid, attempts)
            self._replace_snippets(rid, snippets)
        self.reindex_fts([rid])
        return rid

    def update(self, record_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        current = self.get(record_id)
        if current is None:
            return None

        allowed = {
            "record_type", "title", "status", "category", "project",
            "search_text", "error_excerpt", "error_fp", "confidence",
        }
        sets: list[str] = []
        params: list[Any] = []

        for key in allowed:
            if key in patch:
                sets.append(f"{key} = ?")
                params.append(patch[key])

        for key, column in (("systems", "systems_json"), ("tags", "tags_json"),
                            ("missing", "missing_json")):
            if key in patch:
                sets.append(f"{column} = ?")
                params.append(_dump_json(patch[key] or []))

        if "payload" in patch:
            merged = {**current["payload"], **(patch["payload"] or {})}
            sets.append("payload_json = ?")
            params.append(json.dumps(merged, ensure_ascii=False))

        if not sets and "attempts" not in patch and "snippets" not in patch:
            return current

        with self.conn:
            if sets:
                sets.append("rev = rev + 1")
                sets.append("dirty = 1")
                sets.append("updated_at = ?")
                params.append(now_ms())
                params.append(record_id)
                self.conn.execute(
                    f"UPDATE records SET {', '.join(sets)} WHERE id = ?",  # noqa: S608
                    params,
                )
            if "attempts" in patch:
                self._replace_attempts(record_id, patch["attempts"] or [])
            if "snippets" in patch:
                self._replace_snippets(record_id, patch["snippets"] or [])

        self.reindex_fts([record_id])
        return self.get(record_id)

    def _replace_attempts(self, record_id: str, attempts: Iterable[dict[str, Any]]) -> None:
        self.conn.execute("DELETE FROM attempts WHERE record_id = ?", (record_id,))
        for i, a in enumerate(attempts):
            self.conn.execute(
                """
                INSERT INTO attempts (id, record_id, seq, hypothesis, action, observation, worked, elapsed_min)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    a.get("id") or new_id(),
                    record_id,
                    a.get("seq") if a.get("seq") is not None else i,
                    a.get("hypothesis"),
                    a.get("action"),
                    a.get("observation"),
                    Worked.coerce(a.get("worked", 0)),
                    a.get("elapsed_min"),
                ),
            )

    def _replace_snippets(self, record_id: str, snippets: Iterable[dict[str, Any]]) -> None:
        self.conn.execute("DELETE FROM snippets WHERE record_id = ?", (record_id,))
        for s in snippets:
            self.conn.execute(
                "INSERT INTO snippets (id, record_id, kind, lang, body, note) VALUES (?,?,?,?,?,?)",
                (s.get("id") or new_id(), record_id, s.get("kind"), s.get("lang"),
                 s.get("body", ""), s.get("note")),
            )

    def soft_delete(self, record_id: str) -> bool:
        ts = now_ms()
        with self.conn:
            cur = self.conn.execute(
                "UPDATE records SET deleted_at = ?, rev = rev + 1, dirty = 1, updated_at = ? "
                "WHERE id = ? AND deleted_at IS NULL",
                (ts, ts, record_id),
            )
        if cur.rowcount:
            self.conn.execute("DELETE FROM records_fts WHERE record_id = ?", (record_id,))
            self.conn.commit()
            return True
        return False

    # ── 读 ───────────────────────────────────────────────────────

    def get(self, record_id: str, *, include_deleted: bool = False) -> dict[str, Any] | None:
        sql = f"SELECT {_LIST_COLUMNS} FROM records WHERE id = ?"
        if not include_deleted:
            sql += " AND deleted_at IS NULL"
        row = self.conn.execute(sql, (record_id,)).fetchone()
        if row is None:
            return None
        data = _row_to_dict(row)
        data["attempts"] = self._attempts(record_id)
        data["snippets"] = self._snippets(record_id)
        self.conn.execute("UPDATE records SET hit_count = hit_count + 1 WHERE id = ?", (record_id,))
        self.conn.commit()
        return data

    def _attempts(self, record_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT id, seq, hypothesis, action, observation, worked, elapsed_min "
            "FROM attempts WHERE record_id = ? ORDER BY seq",
            (record_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def _snippets(self, record_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT id, kind, lang, body, note, copy_count FROM snippets "
            "WHERE record_id = ? ORDER BY rowid",
            (record_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list(self, filters: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
        where: list[str] = ["deleted_at IS NULL"]
        params: list[Any] = []

        for key in ("record_type", "category", "project", "status"):
            if filters.get(key):
                where.append(f"{key} = ?")
                params.append(filters[key])

        if filters.get("system"):
            where.append(
                "EXISTS (SELECT 1 FROM json_each(systems_json) WHERE json_each.value = ?)"
            )
            params.append(filters["system"])

        if filters.get("tag"):
            where.append("EXISTS (SELECT 1 FROM json_each(tags_json) WHERE json_each.value = ?)")
            params.append(filters["tag"])

        if filters.get("dirty") is not None:
            where.append("dirty = ?")
            params.append(int(filters["dirty"]))

        keyword = (filters.get("q") or "").strip()
        if keyword:
            where.append("(title LIKE ? OR search_text LIKE ? OR IFNULL(error_excerpt,'') LIKE ?)")
            like = f"%{keyword}%"
            params.extend([like, like, like])

        clause = " AND ".join(where)
        total = self.conn.execute(
            f"SELECT COUNT(*) AS c FROM records WHERE {clause}", params  # noqa: S608
        ).fetchone()["c"]

        order = {"updated": "updated_at DESC", "created": "created_at DESC",
                 "hits": "hit_count DESC"}.get(filters.get("order", "updated"), "updated_at DESC")

        limit = int(filters.get("limit", 20))
        offset = int(filters.get("offset", 0))
        rows = self.conn.execute(
            f"SELECT {_LIST_COLUMNS} FROM records WHERE {clause} "  # noqa: S608
            f"ORDER BY {order} LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()

        return [_row_to_dict(r) for r in rows], int(total)

    def search_ids(self, keyword: str, limit: int = 50) -> list[tuple[str, float]]:
        """关键词召回。

        trigram 分词器要求查询词 >= 3 个字符，更短的查询回退到 LIKE。
        P2 阶段会在这里叠加报错指纹与向量召回，接口保持不变。
        """
        keyword = (keyword or "").strip()
        if not keyword:
            return []

        if len(keyword) >= 3:
            quoted = '"' + keyword.replace('"', '""') + '"'
            try:
                rows = self.conn.execute(
                    "SELECT record_id, bm25(records_fts) AS score FROM records_fts "
                    "WHERE records_fts MATCH ? ORDER BY score LIMIT ?",
                    (quoted, limit),
                ).fetchall()
                return [(r["record_id"], float(r["score"])) for r in rows]
            except sqlite3.OperationalError:
                pass  # 查询语法触发异常时回退到 LIKE

        like = f"%{keyword}%"
        rows = self.conn.execute(
            "SELECT id AS record_id FROM records WHERE deleted_at IS NULL "
            "AND (title LIKE ? OR search_text LIKE ?) ORDER BY updated_at DESC LIMIT ?",
            (like, like, limit),
        ).fetchall()
        return [(r["record_id"], 0.0) for r in rows]

    # ── 索引 ─────────────────────────────────────────────────────

    def reindex_fts(self, record_ids: list[str] | None = None) -> int:
        """重建全文索引。

        record_ids 为空表示全库重建 —— 这正是「改完词表一键重跑」的底层能力。
        """
        if record_ids is None:
            self.conn.execute("DELETE FROM records_fts")
            rows = self.conn.execute(
                "SELECT id, title, search_text, error_excerpt FROM records WHERE deleted_at IS NULL"
            ).fetchall()
        else:
            if not record_ids:
                return 0
            for rid in record_ids:
                self.conn.execute("DELETE FROM records_fts WHERE record_id = ?", (rid,))
            marks = ",".join("?" * len(record_ids))
            rows = self.conn.execute(
                "SELECT id, title, search_text, error_excerpt FROM records "
                f"WHERE id IN ({marks}) AND deleted_at IS NULL",  # noqa: S608
                record_ids,
            ).fetchall()

        for r in rows:
            self.conn.execute(
                "INSERT INTO records_fts (record_id, title, search_text, error_excerpt) VALUES (?,?,?,?)",
                (r["id"], r["title"], r["search_text"] or "", r["error_excerpt"] or ""),
            )
        self.conn.commit()
        return len(rows)

    # ── 同步（P4 启用，数据结构现在就定好）────────────────────────

    def changes_since(self, since: int, limit: int = 500) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            f"SELECT {_LIST_COLUMNS} FROM records WHERE updated_at > ? "
            "ORDER BY updated_at ASC LIMIT ?",
            (since, limit),
        ).fetchall()
        out = []
        for r in rows:
            data = _row_to_dict(r)
            if data["deleted_at"] is None:
                data["attempts"] = self._attempts(data["id"])
                data["snippets"] = self._snippets(data["id"])
            out.append(data)
        return out

    def dirty_ids(self, limit: int = 500) -> list[str]:
        rows = self.conn.execute(
            "SELECT id FROM records WHERE dirty = 1 ORDER BY updated_at ASC LIMIT ?", (limit,)
        ).fetchall()
        return [r["id"] for r in rows]

    def mark_clean(self, record_ids: list[str]) -> None:
        if not record_ids:
            return
        marks = ",".join("?" * len(record_ids))
        with self.conn:
            self.conn.execute(
                f"UPDATE records SET dirty = 0 WHERE id IN ({marks})",  # noqa: S608
                record_ids,
            )

    def count_by(self, column: str) -> list[dict[str, Any]]:
        """轻量统计。column 只能是白名单内的列名。"""
        allowed = {"record_type", "category", "project", "status"}
        if column not in allowed:
            raise ValueError(f"不支持按 {column} 统计")
        rows = self.conn.execute(
            f"SELECT {column} AS key, COUNT(*) AS count FROM records "  # noqa: S608
            "WHERE deleted_at IS NULL GROUP BY 1 ORDER BY count DESC"
        ).fetchall()
        return [{"key": r["key"], "count": r["count"]} for r in rows]
