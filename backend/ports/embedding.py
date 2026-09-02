"""向量化端口。

P0 由 NoopEmbedding 占位。P2 换 bge-m3 本地模型或云端 embedding 时，
新增一个 adapter 并改配置即可。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    name: str
    model: str
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量向量化。返回顺序与输入一致。"""
        ...
