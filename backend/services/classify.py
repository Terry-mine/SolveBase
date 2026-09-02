"""类型判定与文本切片。

P0：纯规则（快、离线、可预测）。
P1：换成 LLM 判定 —— 只要保持 `guess_record_type(text) -> str` 这个签名不变，
调用方（capture 服务）一行都不用改。

这就是"逻辑后置"的落地方式：先把接缝留出来。
"""

from __future__ import annotations

import re

from ..domain.enums import RecordType

_ERROR_HINTS = (
    "traceback", "exception", "stacktrace", "panic", "segfault",
    "errno", "econnrefused", "timeout", "refused", "denied", "failed",
    "error:", "error ", "cannot", "could not", "unable to",
    "报错", "异常", "失败", "错误", "无法", "不能", "拒绝", "超时", "崩溃",
)

_RUNBOOK_HINTS = (
    "如何", "怎么", "步骤", "流程", "部署", "发版", "上线", "回滚",
    "初始化", "安装", "扩容", "巡检", "迁移步骤",
)


def guess_record_type(text: str) -> str:
    lower = (text or "").lower()

    error_score = sum(1 for h in _ERROR_HINTS if h in lower)
    if "traceback (most recent call last)" in lower or re.search(r"^\s*at .+\(.+\)", text, re.M):
        error_score += 3
    if re.search(r"\b\w+Error\b|\b\w+Exception\b", text):
        error_score += 2

    runbook_score = sum(1 for h in _RUNBOOK_HINTS if h in lower)

    if error_score >= 2 and error_score >= runbook_score:
        return str(RecordType.INCIDENT)
    if runbook_score >= 1 and runbook_score > error_score:
        return str(RecordType.RUNBOOK)
    return str(RecordType.INCIDENT)


def guess_title(text: str, max_len: int = 80) -> str:
    for line in (text or "").splitlines():
        line = line.strip()
        if line:
            return line[:max_len]
    return "(无标题)"


def extract_error_excerpt(text: str, max_lines: int = 12) -> str | None:
    lines = (text or "").splitlines()
    hits = [ln for ln in lines if any(h in ln.lower() for h in _ERROR_HINTS)]
    if not hits:
        return None
    return "\n".join(hits[:max_lines])
