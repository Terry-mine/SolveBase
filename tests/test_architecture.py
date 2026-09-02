"""架构约束测试。

这些用例保护的不是功能，而是"改一块不用动整体"的前提条件。
任何一条变红，都说明有人在破坏分层。
"""

from __future__ import annotations

from pathlib import Path

import pytest

import backend
from backend.adapters.embedding.noop import NoopEmbedding
from backend.adapters.llm.noop import NoopLLM
from backend.adapters.reranker.noop import NoopReranker
from backend.adapters.sync.noop import NoopSync
from backend.ports.embedding import EmbeddingProvider
from backend.ports.llm import LLMProvider
from backend.ports.reranker import RerankerProvider
from backend.ports.sync import SyncProvider
from backend.services import registry


@pytest.mark.parametrize(
    "impl,port",
    [
        (NoopLLM, LLMProvider),
        (NoopEmbedding, EmbeddingProvider),
        (NoopReranker, RerankerProvider),
        (NoopSync, SyncProvider),
    ],
)
def test_adapter_satisfies_port(impl: type, port: type) -> None:
    assert isinstance(impl(), port)


@pytest.mark.parametrize("kind", ["llm", "embedding", "reranker", "sync"])
def test_every_kind_has_a_noop_default(kind: str) -> None:
    """保证系统在没有任何外部依赖时也能跑起来。"""
    assert "noop" in registry.available_names(kind)


def test_unknown_provider_raises_actionable_error() -> None:
    with pytest.raises(registry.ProviderNotFoundError) as exc:
        registry.create("llm", "does-not-exist")
    assert "已注册" in str(exc.value)


def test_migration_versions_are_unique_and_ordered() -> None:
    from backend.db.migrations.runner import load_migrations

    versions = [m.version for m in load_migrations()]
    assert versions == sorted(versions)
    assert len(versions) == len(set(versions))


def test_domain_and_ports_do_not_depend_on_framework_or_db() -> None:
    """分层铁律：domain / ports 不许碰 fastapi 和 sqlite3。

    这条守住了，换框架、换存储就都是局部改动。
    """
    root = Path(backend.__file__).parent
    for sub in ("domain", "ports"):
        for path in (root / sub).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "import fastapi" not in text, f"{path} 不应依赖 fastapi"
            assert "import sqlite3" not in text, f"{path} 不应依赖 sqlite3"


def test_sql_only_lives_in_repositories() -> None:
    """SQL 只允许出现在 db/ 目录，业务服务不许直接写 SQL。"""
    root = Path(backend.__file__).parent
    offenders = [
        str(p.relative_to(root))
        for p in root.rglob("*.py")
        if "db" not in p.relative_to(root).parts
        and "migrations" not in p.relative_to(root).parts
        and any(k in p.read_text(encoding="utf-8") for k in ("SELECT ", "INSERT INTO", "UPDATE records"))
    ]
    assert offenders == [], f"这些文件不应包含 SQL：{offenders}"


def test_vocab_is_a_closed_set() -> None:
    from backend.domain.vocab import get_vocabulary

    vocab = get_vocabulary()
    for key in vocab.type_keys:
        spec = vocab.get(key)
        codes = spec.category_codes
        assert len(codes) == len(set(codes)), f"{key} 分类 code 重复"
        assert "Other" in codes, f"{key} 缺少 Other 兜底"


def test_every_type_has_a_payload_validator_or_passes_through() -> None:
    """加新记录类型时，payload 校验器缺失不应导致崩溃。"""
    from backend.domain.payloads import validate
    from backend.domain.vocab import get_vocabulary

    for key in get_vocabulary().type_keys:
        out = validate(key, {"任意键": "任意值"})
        assert isinstance(out, dict)
