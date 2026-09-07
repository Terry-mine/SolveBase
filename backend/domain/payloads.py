"""每种记录类型的 payload 形状。

设计意图：records 表用 payload_json 存类型专属内容，
所以「加一种新记录类型」= 在这里注册一个校验函数 + 往 vocab.yaml 加一项，
不需要改表、不需要改主流程。

这里只做"补默认值 + 类型收敛"，不做强校验 —— 个人系统应该容忍残缺，
而不是在录入时把人拦住。
"""

from __future__ import annotations

from typing import Any, Callable

PayloadValidator = Callable[[dict[str, Any]], dict[str, Any]]

_REGISTRY: dict[str, PayloadValidator] = {}


def register(record_type: str) -> Callable[[PayloadValidator], PayloadValidator]:
    def deco(fn: PayloadValidator) -> PayloadValidator:
        _REGISTRY[record_type] = fn
        return fn

    return deco


def validate(record_type: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    """未知类型原样通过，保证加新类型不会让老流程崩。"""
    fn = _REGISTRY.get(record_type)
    data = dict(payload or {})
    out = fn(data) if fn else data
    # 各类型校验器是白名单重建，会把 images 丢掉。
    # images 属跨类型通用资产，统一在这里补回，不必每种类型各写一遍。
    if isinstance(data.get("images"), list):
        out["images"] = data["images"]
    return out


def _text(value: Any, default: str = "") -> str:
    return default if value is None else str(value)


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


@register("incident")
def _incident(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "root_cause": _text(data.get("root_cause")),
        "solution": _text(data.get("solution")),
        "prevention": _text(data.get("prevention")),
        "impact": _text(data.get("impact")),
        "extra": data.get("extra") if isinstance(data.get("extra"), dict) else {},
    }


@register("runbook")
def _runbook(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "preconditions": _list(data.get("preconditions")),
        "steps": _list(data.get("steps")),
        "verify": _text(data.get("verify")),
        "rollback": _text(data.get("rollback")),
        "duration_min": data.get("duration_min"),
        "extra": data.get("extra") if isinstance(data.get("extra"), dict) else {},
    }


@register("note")
def _note(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "conclusion": _text(data.get("conclusion")),
        "scenario": _text(data.get("scenario")),
        "reason": _text(data.get("reason")),
        "extra": data.get("extra") if isinstance(data.get("extra"), dict) else {},
    }
