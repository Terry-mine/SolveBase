"""P0 占位：不产生向量。P2 换成 bge-m3 时新增文件即可。"""

from __future__ import annotations

from ...services.registry import register


@register("embedding", "noop")
class NoopEmbedding:
    name = "noop"
    model = "none"
    dim = 0

    def __init__(self, settings=None, **kwargs) -> None:
        self.settings = settings

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[] for _ in texts]
