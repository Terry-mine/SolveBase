"""LLM 端口。

P0 由 NoopLLM 占位（不联网）。P1 接真实模型时：
    1. 在 backend/adapters/llm/ 下新建一个文件
    2. 用 @register("llm", "deepseek") 装饰
    3. .env 里设 SOLVEBASE_LLM_PROVIDER=deepseek

业务代码一行都不用改。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any] | None = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """返回已解析的 JSON 对象。实现方负责重试与容错。"""
        ...

    def health(self) -> dict[str, Any]:
        ...
