"""按配置构造 provider。

业务代码从这里拿实例，永远不直接 import 具体 adapter。
"""

from __future__ import annotations

from dataclasses import dataclass

from .. import adapters as _adapters  # noqa: F401  导入即触发注册
from ..core.config import Settings, get_settings
from ..ports.embedding import EmbeddingProvider
from ..ports.llm import LLMProvider
from ..ports.reranker import RerankerProvider
from ..ports.sync import SyncProvider
from . import registry


@dataclass(frozen=True)
class Providers:
    llm: LLMProvider
    embedding: EmbeddingProvider
    reranker: RerankerProvider
    sync: SyncProvider


# Settings 不可哈希，所以按 provider 名组合做缓存键
_CACHE: dict[tuple[str, str, str, str], Providers] = {}


def build_providers(settings: Settings) -> Providers:
    key = (
        settings.llm_provider,
        settings.embedding_provider,
        settings.reranker_provider,
        settings.sync_provider,
    )
    if key not in _CACHE:
        _CACHE[key] = Providers(
            llm=registry.create("llm", settings.llm_provider, settings=settings),
            embedding=registry.create("embedding", settings.embedding_provider, settings=settings),
            reranker=registry.create("reranker", settings.reranker_provider, settings=settings),
            sync=registry.create("sync", settings.sync_provider, settings=settings),
        )
    return _CACHE[key]


def get_providers() -> Providers:
    return build_providers(get_settings())


def capabilities() -> dict[str, object]:
    """暴露给 /health，方便一眼看清当前挂的是哪些实现。"""
    settings = get_settings()
    providers = get_providers()
    return {
        "registered": registry.snapshot(),
        "active": {
            "llm": settings.llm_provider,
            "embedding": settings.embedding_provider,
            "reranker": settings.reranker_provider,
            "sync": settings.sync_provider,
        },
        "enabled": {
            "llm": providers.llm.name != "noop",
            "embedding": providers.embedding.name != "noop",
            "reranker": providers.reranker.name != "noop",
            "sync": providers.sync.name != "noop",
        },
    }
