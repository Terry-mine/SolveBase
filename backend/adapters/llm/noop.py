"""P0 占位实现：不做任何 LLM 调用。

存在的意义是让整条链路（capture → 记录落库 → 待规整队列）从第一天就跑通，
后面把 provider 换成真实模型时，上层代码不动。
"""

from __future__ import annotations

from typing import Any

from ...services.registry import register


@register("llm", "noop")
class NoopLLM:
    name = "noop"
    model = "none"

    def __init__(self, settings=None, **kwargs) -> None:
        self.settings = settings

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any] | None = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        return {}

    def health(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.name, "note": "P0 阶段未接入真实模型"}
