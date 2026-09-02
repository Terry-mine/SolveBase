"""版本化迁移。

使用方式（新增字段 / 新表时）：
    1. 在 versions/ 下新建 `002_xxx.py`
    2. 文件里定义 VERSION / DESCRIPTION / up(conn)
    3. 执行 `python -m backend.cli migrate`

规则：已应用的迁移文件**永不修改**。要改结构就加新迁移。
这样任何一台机器从零建库，和一路升级过来的库，结构完全一致。
"""

from __future__ import annotations

import importlib.util
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from ...core.ids import now_ms

VERSIONS_DIR = Path(__file__).parent / "versions"

_CREATE_META = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at  INTEGER NOT NULL
)
"""


@dataclass(frozen=True)
class Migration:
    version: int
    description: str
    module: ModuleType


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"solvebase.migration.{path.stem}", path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"无法加载迁移文件: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_migrations(versions_dir: Path = VERSIONS_DIR) -> list[Migration]:
    items: list[Migration] = []
    for path in sorted(versions_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue
        module = _load_module(path)
        version = getattr(module, "VERSION", None)
        if version is None:
            continue
        items.append(
            Migration(
                version=int(version),
                description=getattr(module, "DESCRIPTION", path.stem),
                module=module,
            )
        )
    items.sort(key=lambda m: m.version)

    seen: set[int] = set()
    for m in items:
        if m.version in seen:
            raise RuntimeError(f"迁移版本号重复: {m.version}")
        seen.add(m.version)
    return items


def applied_versions(conn: sqlite3.Connection) -> list[int]:
    conn.execute(_CREATE_META)
    rows = conn.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
    return [int(r["version"]) for r in rows]


def migrate(conn: sqlite3.Connection, versions_dir: Path = VERSIONS_DIR) -> list[Migration]:
    """应用所有未执行的迁移，返回本次实际执行的列表。"""
    done = set(applied_versions(conn))
    executed: list[Migration] = []

    for m in load_migrations(versions_dir):
        if m.version in done:
            continue
        up = getattr(m.module, "up", None)
        if up is None:
            continue
        with conn:  # 事务：迁移要么全成功要么全回滚
            up(conn)
            conn.execute(
                "INSERT INTO schema_migrations (version, description, applied_at) VALUES (?, ?, ?)",
                (m.version, m.description, now_ms()),
            )
        executed.append(m)

    return executed
