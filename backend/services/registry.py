"""Provider 注册中心。

这是"换实现不改业务代码"的关键：业务层只依赖 ports 里的抽象，
具体实现类在 import 时用装饰器自行登记，运行时按配置里的名字取。

新增一个实现：
    from ...services.registry import register

    @register("llm", "deepseek")
    class DeepSeekLLM:
        ...

然后 .env 里把 SOLVEBASE_LLM_PROVIDER 改成 deepseek。
"""

from __future__ import annotations

from typing import Any, Callable

_REGISTRY: dict[str, dict[str, Any]] = {}


class ProviderNotFoundError(Exception):
    def __init__(self, kind: str, name: str) -> None:
        available = ", ".join(sorted(available_names(kind))) or "（无）"
        super().__init__(f"未找到 provider：kind={kind} name={name}；已注册：{available}")


def register(kind: str, name: str) -> Callable[[type], type]:
    def deco(cls: type) -> type:
        _REGISTRY.setdefault(kind, {})[name] = cls
        return cls

    return deco


def available_names(kind: str) -> list[str]:
    return list(_REGISTRY.get(kind, {}).keys())


def create(kind: str, name: str, **kwargs: Any) -> Any:
    try:
        cls = _REGISTRY[kind][name]
    except KeyError:
        raise ProviderNotFoundError(kind, name) from None
    return cls(**kwargs)


def snapshot() -> dict[str, list[str]]:
    return {kind: sorted(names) for kind, names in _REGISTRY.items()}
