"""后台启动入口（供 start.bat / 开机自启使用）。

为什么需要这个文件：
用 `pythonw.exe` 运行它，进程**完全没有控制台窗口**（不会在任务栏留一个黑框），
但 uvicorn 的日志仍然会落到 logs/server.log —— 不然出问题时什么线索都没有。

    pythonw.exe scripts/serve_bg.py            用 .env / 默认配置
    pythonw.exe scripts/serve_bg.py --port 9000

前台调试请直接用 `python -m backend.cli serve`，日志打在终端里更方便。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 必须先切目录再导入 backend：配置里的相对路径（data/、config/vocab.yaml）都以项目根为基准
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "server.log"
MAX_LOG_BYTES = 2 * 1024 * 1024  # 超过 2MB 就轮转一次，避免无限膨胀


def _redirect_output() -> None:
    """把 stdout/stderr 接到日志文件。

    pythonw.exe 下 sys.stdout/sys.stderr 是 None，不接的话 uvicorn 的日志直接消失。
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_BYTES:
        old = LOG_DIR / "server.log.1"
        old.unlink(missing_ok=True)
        LOG_FILE.rename(old)
    # buffering=1 = 行缓冲，崩溃时最后几行也能落盘
    stream = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
    sys.stdout = stream
    sys.stderr = stream


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SolveBase 后台启动")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args(argv)

    _redirect_output()

    from backend.core.config import get_settings  # noqa: PLC0415  切目录后再导入

    settings = get_settings()
    host = args.host or settings.host
    port = args.port or settings.port

    print(f"--- SolveBase 启动 host={host} port={port} 数据库={settings.database_path} ---")

    import uvicorn  # noqa: PLC0415

    uvicorn.run("backend.main:app", host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
