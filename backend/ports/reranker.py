"""精排端口。

P0 由 NoopReranker 占位（按原顺序返回）。P2 换 bge-reranker-v2-m3 时，
新增 adapter 改配置，检索服务不用动。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class RerankerProvider(Protocol):
    name: str

    def rerank(self, query: str, docs: list[str]) -> list[float]:
        """返回与 docs 等长的相关性分数，越大越相关。"""
        ...
