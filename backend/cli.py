"""命令行入口。

    python -m backend.cli info      看当前状态
    python -m backend.cli migrate   应用数据库迁移
    python -m backend.cli seed      把 vocab.yaml 灌进 vocab 表
    python -m backend.cli reindex   重建全文索引
    python -m backend.cli audit     检查词表
    python -m backend.cli serve     启动服务
"""

from __future__ import annotations

import argparse
import json
import sys

from .core.config import get_settings
from .db.connection import connect
from .db.migrations.runner import applied_versions, migrate
from .db.repositories.records import RecordRepository
from .domain.vocab import audit, get_vocabulary
from .services.providers import capabilities
from .services.seed import seed_vocabulary


def _conn():
    settings = get_settings()
    settings.ensure_dirs()
    return connect(settings.database_path), settings


def cmd_info(args: argparse.Namespace) -> int:
    conn, settings = _conn()
    try:
        versions = applied_versions(conn)
        vocab = get_vocabulary()
        info = {
            "app": settings.app_name,
            "version": settings.app_version,
            "database": str(settings.database_path),
            "device_id": settings.device_id,
            "migrations_applied": versions,
            "vocab": {"version": vocab.version, "types": list(vocab.type_keys)},
            "providers": capabilities(),
            "issues": [{"level": i.level, "message": i.message} for i in audit(vocab)],
        }
    finally:
        conn.close()
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    conn, _ = _conn()
    try:
        done = migrate(conn)
    finally:
        conn.close()
    if done:
        for m in done:
            print(f"已应用迁移 {m.version}: {m.description}")
    else:
        print("已是最新，无需迁移")
    return 0


def cmd_seed(args: argparse.Namespace) -> int:
    conn, _ = _conn()
    try:
        result = seed_vocabulary(conn)
    finally:
        conn.close()
    print(f"词表 v{result['vocab_version']} 已写入，共 {result['rows_written']} 行")
    for issue in result["issues"]:
        print(f"  [{issue['level']}] {issue['message']}")
    return 0


def cmd_reindex(args: argparse.Namespace) -> int:
    conn, settings = _conn()
    try:
        repo = RecordRepository(conn, device_id=settings.device_id, schema_ver=settings.schema_ver)
        count = repo.reindex_fts(None)
    finally:
        conn.close()
    print(f"全文索引已重建，共 {count} 条")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    issues = audit(get_vocabulary())
    if not issues:
        print("词表检查通过")
        return 0
    for i in issues:
        print(f"[{i.level}] {i.message}")
    return 1 if any(i.level == "error" for i in issues) else 0


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=args.host or settings.host,
        port=args.port or settings.port,
        reload=bool(args.reload),
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="solvebase", description="SolveBase 命令行")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("info", help="查看当前状态").set_defaults(func=cmd_info)
    sub.add_parser("migrate", help="应用数据库迁移").set_defaults(func=cmd_migrate)
    sub.add_parser("seed", help="把 vocab.yaml 写入数据库").set_defaults(func=cmd_seed)
    sub.add_parser("reindex", help="重建全文索引").set_defaults(func=cmd_reindex)
    sub.add_parser("audit", help="检查词表").set_defaults(func=cmd_audit)

    serve = sub.add_parser("serve", help="启动服务")
    serve.add_argument("--host", default=None)
    serve.add_argument("--port", type=int, default=None)
    serve.add_argument("--reload", action="store_true")
    serve.set_defaults(func=cmd_serve)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
