"""SQLite 连接。

注意：本项目的多端同步走「记录级 changeset」，绝不通过同步 .db 文件实现。
把 SQLite 文件放进网盘同步目录会导致数据库损坏。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def connect(path: str | Path) -> sqlite3.Connection:
    path = Path(path)
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    # 每个请求一条连接，用完即关。check_same_thread=False 是因为
    # FastAPI 可能在线程池的不同阶段触碰同一条连接。
    conn = sqlite3.connect(str(path), timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn
