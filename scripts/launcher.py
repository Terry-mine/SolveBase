"""SolveBase 启动器 —— start / stop / status / 开机自启。

为什么把逻辑从 .bat 搬到这里（改动前必读，别再退回 .bat 里堆逻辑）：

1. **乱码**：.bat 存成 UTF-8 无 BOM，却靠 `chcp 65001` 撑中文。cmd.exe 在批处理执行
   中途切代码页，后续字节会按错误偏移解析，中文必然乱码（用户实测复现）。
   → 现在 .bat 全是纯 ASCII（只有 3~4 行转发），中文只出现在本文件里。
2. **健康检查不可靠**：原来用 `curl` + `ping -n` 轮询，机器上没有 curl 就必然超时失败。
   → 现在用 urllib，零外部依赖。
3. **失败无声**：pythonw 没窗口，进程悄悄死了谁也不知道。
   → 现在每次动作都写 logs/launcher.log，起不来会把 server.log 尾部贴出来。
4. **重复启动**：端口被占时新实例抢不到端口，报 10048 后**静默退出**，
   用户看到的就是"页面消失了"。
   → 现在启动前先探活：活着就复用，僵尸才清理，且启动后监视进程是否早退。

用法（.bat 已封装，一般不直接调）：
    python scripts/launcher.py start     启动（若已在运行则复用）并打开浏览器
    python scripts/launcher.py start --no-browser
    python scripts/launcher.py stop      停止 8787 / 5173
    python scripts/launcher.py status    查看运行状态
    python scripts/launcher.py install-autostart    注册开机自启
    python scripts/launcher.py uninstall-autostart  取消开机自启

pythonw 下运行（开机自启走这条）：没有 stdout，所有输出只进 launcher.log。
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SERVE_BG = SCRIPTS / "serve_bg.py"
LOG_DIR = ROOT / "logs"
LAUNCHER_LOG = LOG_DIR / "launcher.log"
SERVER_LOG = LOG_DIR / "server.log"
DIST_INDEX = ROOT / "web" / "dist" / "index.html"

VENV_DIR = Path.home() / ".workbuddy" / "binaries" / "python" / "envs" / "default" / "Scripts"
PYW = VENV_DIR / "pythonw.exe"  # 无窗口，跑服务
PY = VENV_DIR / "python.exe"  # 有窗口，跑启动器本身（要显示中文提示）

# 单进程模式的生产端口；5173 只在开发模式出现，stop 时一并清理
MAIN_PORT = 8787
DEV_PORT = 5173

# Windows 进程创建标志：脱离调用方控制台，父进程退出后服务继续存活
DETACHED = 0x00000008  # DETACHED_PROCESS
NEW_CONSOLE = 0x00000010  # CREATE_NEW_CONSOLE，开发模式给后端/前端各开一个窗口

# 构建前端用的 Node（只 build / dev 用得到，日常启动不需要 Node）
NODE_DIR = Path.home() / ".workbuddy" / "binaries" / "node" / "versions" / "22.22.2"


# ---------------------------------------------------------------- 输出与日志


def _setup_console() -> None:
    """让中文能正常显示。pythonw 下 sys.stdout 是 None，全部跳过。"""
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except Exception:
            pass  # pythonw 下 stream 是 None


def _log(msg: str = "") -> None:
    """同时写 launcher.log 和控制台。

    写文件这一步不能省：开机自启跑在 pythonw 下没有控制台，
    不落盘的话出问题永远查不到。
    """
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LAUNCHER_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {msg}\n")
    except Exception:
        pass
    if sys.stdout is not None:
        print(msg)


def _server_log_tail(lines: int = 15) -> str:
    """取 server.log 末尾几行，启动失败时用来定位真凶。"""
    try:
        if not SERVER_LOG.exists():
            return "（server.log 不存在，服务进程可能根本没启动）"
        text = SERVER_LOG.read_text(encoding="utf-8", errors="replace")
        return "\n".join(text.splitlines()[-lines:])
    except Exception as exc:  # pragma: no cover
        return f"（读取 server.log 失败：{exc}）"


# ---------------------------------------------------------------- 端口与进程


def _run(cmd: list[str], timeout: int = 20) -> str:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, encoding="gbk", errors="replace", timeout=timeout
        )
        return r.stdout or ""
    except Exception as exc:
        return f"__ERR__{exc}"


def _pids_on_port(port: int) -> list[str]:
    """返回监听该端口的 PID 列表（去重、保序）。"""
    out = _run(["netstat", "-ano", "-p", "tcp"])
    pids: list[str] = []
    for line in out.splitlines():
        if "LISTENING" not in line.upper():
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        local = parts[1]
        # 兼容 127.0.0.1:8787 与 [::1]:8787
        if local.rsplit(":", 1)[-1] != str(port):
            continue
        pid = parts[-1]
        if pid.isdigit() and pid not in pids:
            pids.append(pid)
    return pids


def _pids_running_serve_bg() -> list[str]:
    """找出所有在跑 serve_bg.py 的 pythonw 进程（不论占没占端口）。

    为什么要这个：抢端口失败的实例（日志里那条 10048）有时不会干净退出，
    会变成不占端口的僵尸留在后台。它们越积越多，下次启动更容易再次冲突。
    """
    out = _run(["wmic", "process", "where", "name='pythonw.exe'", "get",
                "ProcessId,CommandLine", "/format:list"])
    pids: list[str] = []
    cmdline: str | None = None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("CommandLine="):
            cmdline = line[len("CommandLine="):]
        elif line.startswith("ProcessId="):
            pid = line[len("ProcessId="):].strip()
            if pid.isdigit() and cmdline and "serve_bg.py" in cmdline:
                pids.append(pid)
            cmdline = None
    return pids


def _pid_alive(pid: str) -> bool:
    out = _run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], timeout=15)
    return pid in out


def _kill(pid: str) -> bool:
    """杀进程（连带子进程树），返回是否真的清掉了。

    两个坑，都踩过：
    1. 不看 taskkill 的返回文案 —— 杀子进程时父进程往往正在自行退出，
       taskkill 会报"找不到进程"，但那其实是成功。以进程是否还在为准。
    2. taskkill /F 的终止不是瞬时的，立刻查会查到"还在"，误报失败。
       这里给 2 秒宽限期轮询。
    """
    _run(["taskkill", "/PID", pid, "/F", "/T"], timeout=15)
    for _ in range(8):
        if not _pid_alive(pid):
            return True
        time.sleep(0.25)
    return not _pid_alive(pid)


def _health(port: int, timeout: float = 2.0) -> bool:
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/v1/health", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _api_get(port: int, path: str, timeout: float = 5.0):
    import json
    import urllib.request

    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _open_browser(port: int) -> None:
    url = f"http://127.0.0.1:{port}"
    try:
        os.startfile(url)  # type: ignore[attr-defined]  # 用系统默认浏览器打开
        _log(f"已打开浏览器：{url}")
    except Exception as exc:
        _log(f"打开浏览器失败（服务不受影响）：{exc}\n  手动访问：{url}")


# ---------------------------------------------------------------- 子命令


def _wait_ready(proc: subprocess.Popen, port: int, timeout: int = 30) -> tuple[bool, str]:
    """等服务就绪，同时盯住进程是不是早退了。

    返回 (是否就绪, 失败原因)。这是修掉"页面消失"的关键：
    进程若悄悄退出（例如端口被占 10048），立刻把 server.log 尾部捞出来。
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _health(port, timeout=1.5):
            return True, ""
        code = proc.poll()
        if code is not None:
            return False, f"服务进程启动后立刻退出（返回码 {code}）"
        time.sleep(0.5)
    return False, f"等待 {timeout} 秒仍未就绪"


def cmd_start(open_browser: bool = True, attempts: int = 2) -> int:
    port = MAIN_PORT
    _log(f"=== start 目标端口 {port} ===")

    if not PYW.exists():
        _log(f"[错误] 找不到 pythonw：{PYW}\n  环境换过的话改 scripts/launcher.py 顶部的 VENV_DIR")
        return 1

    # 1) 已经在跑就复用，绝不启动第二个（第二个必然 10048 静默死掉）
    if _health(port):
        pids = _pids_on_port(port)
        _log(f"服务已在运行（PID {','.join(pids) or '未知'}），直接复用，不重复启动")
        return _after_ready(port, open_browser)

    # 2) 端口被占但没响应 = 僵尸进程，清掉再起
    for pid in _pids_on_port(port):
        _log(f"端口 {port} 被无响应的进程占用（PID {pid}），先清理")
        _kill(pid)
        time.sleep(1)

    # 2b) 清理没占端口的残留实例。
    #     uvicorn 在 Windows 下是两层进程：父进程 wrapper + 子进程真正监听端口
    #     （实测如此，与 reload/workers 无关，属 uvicorn 在 Windows 的固有行为）。
    #     上次若只清掉其中一层，另一层会留成占着日志却不干活的僵尸，越积越多。
    stale = _pids_running_serve_bg()
    if stale:
        _log(f"发现 {len(stale)} 个残留服务进程（{', '.join(stale)}），先清理")
        for pid in stale:
            _kill(pid)
        time.sleep(1)

    if not DIST_INDEX.exists():
        _log(f"[提示] 没找到 {DIST_INDEX}，界面打不开（API 仍可用）。改过前端请运行 build.bat")

    # 3) 启动，最多 attempts 次（开机瞬间系统资源没就绪，重试一次很值）
    for attempt in range(1, attempts + 1):
        _log(f"启动服务（第 {attempt}/{attempts} 次）...")
        try:
            proc = subprocess.Popen(
                [str(PYW), str(SERVE_BG)],
                cwd=str(ROOT),
                creationflags=DETACHED if sys.platform == "win32" else 0,
            )
        except Exception as exc:
            _log(f"[错误] 无法启动服务进程：{exc}")
            return 1

        ok, reason = _wait_ready(proc, port)
        if ok:
            _log(f"服务已就绪（PID {proc.pid}）")
            return _after_ready(port, open_browser)

        _log(f"[失败] {reason}")
        _log("server.log 尾部：\n" + _server_log_tail())
        if attempt < attempts:
            _log("2 秒后重试...")
            time.sleep(2)

    _log(f"[放弃] 服务没能起来。完整日志见 {LAUNCHER_LOG} 和 {SERVER_LOG}")
    return 1


def _after_ready(port: int, open_browser: bool) -> int:
    """服务就绪后做一次真实读库校验，并开浏览器。

    用户报过"加载不了数据库"，所以这里不只看 /health，
    还要真的查一次记录接口，把后端错误暴露到日志里。
    """
    try:
        data = _api_get(port, "/api/v1/records?limit=1")
        total = None
        if isinstance(data, dict):
            total = data.get("total")
            if total is None and isinstance(data.get("items"), list):
                total = len(data["items"])
        _log(f"数据库读取校验通过（records 接口正常，total={total}）")
    except Exception as exc:
        _log(f"[警告] 服务已起，但读取记录接口失败：{exc}\n  数据库文件：{ROOT / 'data' / 'solvebase.db'}")

    if open_browser:
        _open_browser(port)
    return 0


def cmd_stop() -> int:
    _log("=== stop ===")
    targets: list[tuple[str, str]] = []  # (pid, 来源)
    for port in (MAIN_PORT, DEV_PORT):
        pids = _pids_on_port(port)
        if not pids:
            _log(f"端口 {port}：没有服务在监听")
        for pid in pids:
            targets.append((pid, f"端口 {port}"))

    # 没占端口却还活着的 serve_bg 残留进程，一并清掉，避免越积越多
    known = {p for p, _ in targets}
    for pid in _pids_running_serve_bg():
        if pid not in known:
            targets.append((pid, "残留服务进程"))
            known.add(pid)

    if not targets:
        _log("SolveBase 本来就没在运行。")
        return 0

    for pid, src in targets:
        _log(f"停止 {src} PID {pid}")
        ok = _kill(pid)
        _log("  已停止" if ok else "  未能停止（进程仍在运行）")

    # 等端口真正释放
    for _ in range(12):
        if not _pids_on_port(MAIN_PORT) and not _pids_on_port(DEV_PORT):
            break
        time.sleep(0.5)

    left = _pids_running_serve_bg()
    _log("已全部停止。" if not left else f"仍有残留进程未退出：{', '.join(left)}")
    # 不在这里暂停：stop.bat / status.bat 会自己 pause，避免双重提示
    return 0


def cmd_status() -> int:
    _log("=== status ===")
    for port in (MAIN_PORT, DEV_PORT):
        pids = _pids_on_port(port)
        alive = _health(port)
        if not pids:
            _log(f"端口 {port}：未运行")
            continue
        state = "健康" if alive else "端口被占但没有响应（僵尸进程）"
        _log(f"端口 {port}：运行中 PID {','.join(pids)}  状态={state}")

    db = ROOT / "data" / "solvebase.db"
    if db.exists():
        _log(f"数据库：{db}（{db.stat().st_size} 字节）")
    else:
        _log(f"数据库：不存在（{db}）")

    if _health(MAIN_PORT):
        try:
            stats = _api_get(MAIN_PORT, "/api/v1/records/stats")
            _log(f"记录统计：{stats}")
        except Exception as exc:
            _log(f"读取统计失败：{exc}")
    return 0


# ---------------------------------------------------------------- 开机自启


def _startup_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return Path(base) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _vbs_content() -> str:
    """生成开机自启 vbs。内容保持纯 ASCII（vbs 按系统 ANSI 读，写中文必炸）。"""
    q = lambda s: '"' + s.replace('"', '""') + '"'  # noqa: E731
    inner = f"{q(str(PYW))} {q(str(SCRIPTS / 'launcher.py'))} start"
    run_arg = '"' + inner.replace('"', '""') + '"'
    return (
        "' SolveBase auto-start - generated by scripts/launcher.py\n"
        "' Delete this file to disable auto-start.\n"
        "Set sh = CreateObject(\"WScript.Shell\")\n"
        f"sh.Run {run_arg}, 0, False\n"
    )


def cmd_install_autostart() -> int:
    target = _startup_dir() / "SolveBase.vbs"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_vbs_content(), encoding="ascii")
    except Exception as exc:
        _log(f"[失败] 写入启动文件夹被拒：{exc}\n  路径：{target}")
        return 1
    _log(f"开机自启已注册：{target}")
    _log(f"  开机时会无窗口执行：{PYW} {SCRIPTS / 'launcher.py'} start")
    _log("  启动结果记录在 logs/launcher.log，出问题先看它。")
    return 0


def cmd_uninstall_autostart() -> int:
    hits = []
    for name in ("SolveBase.vbs", "SolveBase.lnk"):
        p = _startup_dir() / name
        if p.exists():
            p.unlink()
            hits.append(str(p))
    if hits:
        _log("已取消开机自启，删除了：\n  " + "\n  ".join(hits))
    else:
        _log("本来就没有注册开机自启。")
    return 0


# ---------------------------------------------------------------- 构建 / 开发模式


def _npm_env() -> dict:
    env = os.environ.copy()
    env["PATH"] = str(NODE_DIR) + os.pathsep + env.get("PATH", "")
    return env


def cmd_build() -> int:
    """重建前端产物 web/dist。改过 web/src 之后需要跑。"""
    web = ROOT / "web"
    _log("=== build ===")
    if not NODE_DIR.exists():
        _log(f"[错误] 找不到 Node：{NODE_DIR}\n  换过环境请改 scripts/launcher.py 的 NODE_DIR")
        return 1

    env = _npm_env()
    if not (web / "node_modules").exists():
        _log("首次构建，先安装依赖 ...")
        if subprocess.run(f'"{NODE_DIR / "npm.cmd"}" install --no-audit --no-fund',
                          cwd=str(web), env=env, shell=True).returncode:
            _log("[失败] 依赖安装没通过，看上面的报错。")
            return 1

    dist = web / "dist"
    if dist.exists():
        import shutil

        _log("清理旧产物 ...")
        shutil.rmtree(dist, ignore_errors=True)

    _log("构建中 ...")
    if subprocess.run(f'"{NODE_DIR / "npm.cmd"}" run build',
                      cwd=str(web), env=env, shell=True).returncode:
        _log("[失败] 构建没通过，看上面的报错。")
        return 1

    _log("构建完成。重启 SolveBase（stop.bat 再 start.bat）即生效。")
    return 0


def cmd_dev() -> int:
    """开发模式：后端 8787(--reload) + 前端 5173(vite 热更新)，各开一个窗口。"""
    _log("=== dev ===")
    if not NODE_DIR.exists():
        _log(f"[错误] 找不到 Node：{NODE_DIR}")
        return 1

    if _pids_on_port(MAIN_PORT):
        _log(f"[跳过] 后端 {MAIN_PORT} 已在运行")
    else:
        _log(f"启动后端 {MAIN_PORT} ...")
        subprocess.Popen(
            [str(PY), "-m", "uvicorn", "backend.main:app",
             "--host", "127.0.0.1", "--port", str(MAIN_PORT), "--reload"],
            cwd=str(ROOT), creationflags=NEW_CONSOLE,
        )

    if _pids_on_port(DEV_PORT):
        _log(f"[跳过] 前端 {DEV_PORT} 已在运行")
    else:
        _log(f"启动前端 {DEV_PORT} ...")
        subprocess.Popen(
            f'cd /d "{ROOT / "web"}" && "{NODE_DIR / "npm.cmd"}" run dev',
            cwd=str(ROOT / "web"), env=_npm_env(),
            creationflags=NEW_CONSOLE, shell=True,
        )

    # 等前端起来再开浏览器
    for _ in range(30):
        if _pids_on_port(DEV_PORT):
            break
        time.sleep(1)
    _open_browser(DEV_PORT)
    _log(f"开发模式就绪：前端 http://127.0.0.1:{DEV_PORT}（API 已代理到 {MAIN_PORT}）")
    return 0


# ---------------------------------------------------------------- 入口


def main(argv: list[str] | None = None) -> int:
    _setup_console()
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = args[0] if args else "start"
    flags = args[1:]

    table = {
        "start": lambda: cmd_start(open_browser="--no-browser" not in flags),
        "stop": cmd_stop,
        "status": cmd_status,
        "build": cmd_build,
        "dev": cmd_dev,
        "install-autostart": cmd_install_autostart,
        "uninstall-autostart": cmd_uninstall_autostart,
    }
    if cmd not in table:
        _log(f"未知命令：{cmd}\n可用：{' / '.join(table)}")
        return 2
    return table[cmd]()


if __name__ == "__main__":
    sys.exit(main())
