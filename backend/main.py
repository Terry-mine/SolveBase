"""应用组装 —— 全项目唯一的组装点。

换 provider、加路由、加中间件，都只在这里改一处。
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.router import api_router
from .api.webui import mount_webui
from .core.config import Settings, get_settings
from .db.connection import connect
from .db.migrations.runner import migrate
from .services.seed import seed_vocabulary


def bootstrap_database(settings: Settings) -> None:
    """启动时自动建库/迁移/灌词表。

    个人工具优先保证"打开就能用"，避免每次手动敲命令。
    """
    settings.ensure_dirs()
    conn = connect(settings.database_path)
    try:
        migrate(conn)
        seed_vocabulary(conn)
    finally:
        conn.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    if settings.auto_migrate:
        bootstrap_database(settings)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="解题过程自动规整 + 极速检索",
    )

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router, prefix=settings.api_prefix)

    # 前端托管必须放在 API 路由之后：catch-all 路由会吞掉先前未注册的路径。
    webui_mounted = False
    if settings.serve_webui:
        webui_mounted = mount_webui(app, settings.web_dist_dir)

    if not webui_mounted:
        # 没有前端产物（或主动关掉）时，根路径返回自述信息，方便确认服务活着
        @app.get("/", tags=["system"])
        def root() -> dict:
            return {
                "app": settings.app_name,
                "version": settings.app_version,
                "api": settings.api_prefix,
                "docs": "/docs",
                "webui": "未构建，执行 cd web && npm run build 后重启即可在本端口直接打开界面",
            }

    return app


app = create_app()
