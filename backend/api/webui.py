"""托管前端构建产物（web/dist）。

存在的意义：让「开机自启」只需要拉起一个进程。
后端同时提供 API 和界面，浏览器直接开 http://127.0.0.1:8787 即可，运行期不依赖 Node。

设计约束：
- 这是可选能力。dist 不存在时静默跳过，不影响纯 API 使用（settings.serve_webui=False 亦可关掉）。
- 必须在 api_router 之后挂载，否则 catch-all 会吞掉 /api/v1/*。
- catch-all 只对 GET 生效，且遇到 api / docs 前缀一律放行给 404，避免掩盖真实的接口错误。
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# 这些前缀永远不走 SPA 回退：它们属于后端，缺失就该报 404
_RESERVED_PREFIXES = ("api", "docs", "redoc", "openapi.json")


def _is_reserved(path: str) -> bool:
    head = path.lstrip("/").split("/", 1)[0]
    return head in _RESERVED_PREFIXES


def mount_webui(app: FastAPI, dist_dir: Path) -> bool:
    """把 dist_dir 挂到根路径上。返回是否真的挂上了。"""
    index_file = dist_dir / "index.html"
    if not index_file.is_file():
        return False

    dist_root = dist_dir.resolve()

    # Vite 默认把带 hash 的静态资源放在 dist/assets
    assets_dir = dist_dir / "assets"
    if assets_dir.is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=str(assets_dir)),
            name="webui-assets",
        )

    @app.get("/", include_in_schema=False)
    def webui_index() -> FileResponse:
        return FileResponse(index_file)

    @app.get("/{full_path:path}", include_in_schema=False)
    def webui_spa_fallback(full_path: str) -> FileResponse:
        if _is_reserved(full_path):
            raise HTTPException(status_code=404, detail="Not Found")

        candidate = (dist_dir / full_path).resolve()
        # 目录穿越防护：必须落在 dist 内部
        if candidate.is_file() and dist_root in candidate.parents:
            return FileResponse(candidate)

        # 其余交给前端路由（SPA 刷新任意 URL 都能正常打开）
        return FileResponse(index_file)

    return True
