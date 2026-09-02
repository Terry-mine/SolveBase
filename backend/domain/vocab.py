"""受控词表：加载、校验、同义词归并。

事实来源是 config/vocab.yaml。改分类不必碰代码，改完执行
`python -m backend.cli seed` 即可生效。

这里提供的 normalize_* 是「分类自动归并」的字面匹配基础：
LLM 输出自由文本后，先在这里收敛回标准 code，收敛不到才进人工队列。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..core.config import get_settings


class VocabError(Exception):
    """词表本身有问题（文件缺失、结构错误）。"""


class UnknownRecordTypeError(VocabError):
    pass


def _norm(text: str) -> str:
    """归一化：小写、去空白与分隔符。用于容错匹配。"""
    out = []
    for ch in str(text).lower().strip():
        if ch.isalnum():
            out.append(ch)
    return "".join(out)


@dataclass(frozen=True)
class Category:
    code: str
    label: str
    desc: str = ""
    aliases: tuple[str, ...] = ()
    deprecated: bool = False


@dataclass(frozen=True)
class StatusOption:
    code: str
    label: str
    desc: str = ""
    aliases: tuple[str, ...] = ()

    def matches(self, target: str) -> bool:
        return any(_norm(x) == target for x in (self.code, self.label, *self.aliases))


@dataclass(frozen=True)
class TypeSpec:
    key: str
    label: str
    desc: str = ""
    statuses: tuple[StatusOption, ...] = ()
    categories: tuple[Category, ...] = ()

    @property
    def category_codes(self) -> tuple[str, ...]:
        return tuple(c.code for c in self.categories)

    @property
    def status_codes(self) -> tuple[str, ...]:
        return tuple(s.code for s in self.statuses)

    def find_category(self, raw: str | None) -> Category | None:
        """按 code / label / alias 把自由文本收敛回标准分类。"""
        if not raw:
            return None
        target = _norm(raw)
        if not target:
            return None
        for c in self.categories:
            if _norm(c.code) == target:
                return c
        for c in self.categories:
            if _norm(c.label) == target:
                return c
        for c in self.categories:
            if any(_norm(a) == target for a in c.aliases):
                return c
        return None


@dataclass(frozen=True)
class Vocabulary:
    version: int
    types: dict[str, TypeSpec]
    common_statuses: tuple[StatusOption, ...] = ()

    @property
    def type_keys(self) -> tuple[str, ...]:
        return tuple(self.types.keys())

    def get(self, type_key: str) -> TypeSpec:
        try:
            return self.types[type_key]
        except KeyError:
            raise UnknownRecordTypeError(
                f"未知记录类型 '{type_key}'，可选：{', '.join(self.type_keys)}"
            ) from None

    def valid_statuses_for(self, type_key: str) -> tuple[str, ...]:
        spec = self.get(type_key)
        return tuple(s.code for s in self.common_statuses) + spec.status_codes

    def normalize_category(self, type_key: str, raw: str | None) -> str | None:
        found = self.get(type_key).find_category(raw)
        return found.code if found else None

    def normalize_status(self, type_key: str, raw: str | None) -> str | None:
        """按 code 或 label 收敛状态。

        中文场景下 LLM 或前端常给 label（"已解决"），必须收敛回 code（solved），
        否则状态就不是闭集了，统计会散掉。
        """
        if not raw:
            return None
        target = _norm(raw)
        pool = list(self.common_statuses) + list(self.get(type_key).statuses)
        for s in pool:
            if _norm(s.code) == target:
                return s.code
        for s in pool:
            if s.matches(target):
                return s.code
        return None

    def all_rows(self) -> list[dict[str, Any]]:
        """展开成可写入 vocab 表的行。"""
        rows: list[dict[str, Any]] = []
        for key, spec in self.types.items():
            for c in spec.categories:
                rows.append(
                    {
                        "kind": "category",
                        "type_key": key,
                        "code": c.code,
                        "label": c.label,
                        "aliases": list(c.aliases),
                        "deprecated": 1 if c.deprecated else 0,
                    }
                )
            for s in spec.statuses:
                rows.append(
                    {
                        "kind": "status",
                        "type_key": key,
                        "code": s.code,
                        "label": s.label,
                        "aliases": [],
                        "deprecated": 0,
                    }
                )
        for s in self.common_statuses:
            rows.append(
                {
                    "kind": "status",
                    "type_key": "*",
                    "code": s.code,
                    "label": s.label,
                    "aliases": [],
                    "deprecated": 0,
                }
            )
        return rows


def load_vocabulary(path: str | Path) -> Vocabulary:
    path = Path(path)
    if not path.exists():
        raise VocabError(f"词表文件不存在: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if "types" not in data:
        raise VocabError(f"词表缺少 types 字段: {path}")

    types: dict[str, TypeSpec] = {}
    for key, spec in data["types"].items():
        categories = tuple(
            Category(
                code=c["code"],
                label=c.get("label", c["code"]),
                desc=c.get("desc", ""),
                aliases=tuple(c.get("aliases", []) or []),
                deprecated=bool(c.get("deprecated", False)),
            )
            for c in spec.get("categories", []) or []
        )
        statuses = tuple(
            StatusOption(
                code=s["code"],
                label=s.get("label", s["code"]),
                desc=s.get("desc", ""),
                aliases=tuple(s.get("aliases", []) or []),
            )
            for s in spec.get("statuses", []) or []
        )
        types[key] = TypeSpec(
            key=key,
            label=spec.get("label", key),
            desc=spec.get("desc", ""),
            statuses=statuses,
            categories=categories,
        )

    common = tuple(
        StatusOption(
            code=s["code"],
            label=s.get("label", s["code"]),
            desc=s.get("desc", ""),
            aliases=tuple(s.get("aliases", []) or []),
        )
        for s in data.get("common_statuses", []) or []
    )
    return Vocabulary(version=int(data.get("version", 1)), types=types, common_statuses=common)


# 按文件 mtime 缓存：改完 yaml 无需重启进程即可生效
_CACHE: dict[tuple[str, float], Vocabulary] = {}


def get_vocabulary() -> Vocabulary:
    path = Path(get_settings().vocab_path)
    key = (str(path), path.stat().st_mtime if path.exists() else 0.0)
    if key not in _CACHE:
        _CACHE.clear()
        _CACHE[key] = load_vocabulary(path)
    return _CACHE[key]


def clear_vocabulary_cache() -> None:
    _CACHE.clear()


@dataclass(frozen=True)
class VocabIssue:
    level: str
    message: str


def audit(vocab: Vocabulary) -> list[VocabIssue]:
    """词表自检。seed 和启动时都会跑，防止词表写歪了却没人发现。"""
    issues: list[VocabIssue] = []
    for key, spec in vocab.types.items():
        codes = [c.code for c in spec.categories]
        dupes = {c for c in codes if codes.count(c) > 1}
        if dupes:
            issues.append(VocabIssue("error", f"{key} 分类 code 重复: {sorted(dupes)}"))
        if not any(c.code == "Other" for c in spec.categories):
            issues.append(VocabIssue("warn", f"{key} 缺少 Other 兜底分类"))
        for c in spec.categories:
            if not c.desc:
                issues.append(VocabIssue("warn", f"{key}.{c.code} 缺少 desc（会影响 LLM 分类准确率）"))
    return issues
