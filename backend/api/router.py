"""路由聚合。

新增模块只在这里加一行 include_router，不用碰 main.py。
"""

from __future__ import annotations

from fastapi import APIRouter

from .routes import capture, health, records, sync, vocab

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(capture.router)
api_router.include_router(records.router)
api_router.include_router(vocab.router)
api_router.include_router(sync.router)
