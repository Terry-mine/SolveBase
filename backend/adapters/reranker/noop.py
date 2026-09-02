"""P0 占位：按原顺序返回递减分数，等价于不重排。"""

from __future__ import annotations

from ...services.registry import register


@register("reranker", "noop")
class NoopReranker:
    name = "noop"

    def __init__(self, settings=None, **kwargs) -> None:
        self.settings = settings

    def rerank(self, query: str, docs: list[str]) -> list[float]:
        n = len(docs)
        return [float(n - i) for i in range(n)]
