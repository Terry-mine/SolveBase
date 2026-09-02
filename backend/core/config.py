"""集中配置。

所有可调项都在这里，其他模块一律从这里取值。
新增配置项：加一个字段即可，业务代码不需要改。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_prefix="SOLVEBASE_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SolveBase"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    host: str = "127.0.0.1"
    port: int = 8787
    debug: bool = False

    data_dir: Path = PROJECT_ROOT / "data"
    database_path: Path | None = None
    assets_dir: Path | None = None
    vocab_path: Path = PROJECT_ROOT / "config" / "vocab.yaml"

    # 由后端直接托管前端构建产物（web/dist）。
    # 开着 = 单进程模式，只开 8787 就能用整个应用，不需要 Node。
    # 关掉 = 纯 API 模式，前端交给 vite dev / nginx。
    serve_webui: bool = True
    web_dist_dir: Path = PROJECT_ROOT / "web" / "dist"

    # 同步标识：从第一天就有，但 P0 阶段 sync_provider=noop，什么都不做
    device_id: str = "dev-local"
    schema_ver: int = 1

    # 启动时自动 migrate + seed 词表。关掉则需要手动执行 CLI
    auto_migrate: bool = True
    # 前端开发服务器地址，逗号分隔；留空则不加 CORS 中间件
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # 外部能力，全部走 registry 按名字解析，换实现只改这里
    llm_provider: str = "noop"
    embedding_provider: str = "noop"
    reranker_provider: str = "noop"
    sync_provider: str = "noop"

    @model_validator(mode="after")
    def _derive_paths(self) -> "Settings":
        if self.database_path is None:
            self.database_path = self.data_dir / "solvebase.db"
        if self.assets_dir is None:
            self.assets_dir = self.data_dir / "assets"
        return self

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)  # type: ignore[union-attr]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()
