"""前端托管（单进程模式）的契约测试。

锁住四件事，任何一条破了都会让"双击 start.bat 就能用"失效：
1. dist 存在时，根路径返回界面而不是 JSON
2. SPA 任意路径都能回退到 index.html（刷新页面不 404）
3. API / docs 前缀永远不被 SPA 吞掉 —— 接口写错时必须暴露 404，而不是静默返回一张网页
4. dist 不存在时服务照常起，根路径给出自述 JSON
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.core.config import reload_settings
from backend.main import create_app


def _mk_client(tmp_path, monkeypatch, *, with_dist: bool) -> TestClient:
    monkeypatch.setenv("SOLVEBASE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("SOLVEBASE_DATABASE_PATH", str(tmp_path / "data" / "test.db"))
    monkeypatch.setenv("SOLVEBASE_ASSETS_DIR", str(tmp_path / "data" / "assets"))

    dist = tmp_path / "dist"
    if with_dist:
        (dist / "assets").mkdir(parents=True)
        (dist / "index.html").write_text("<!doctype html><title>UI</title>", encoding="utf-8")
        (dist / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    monkeypatch.setenv("SOLVEBASE_WEB_DIST_DIR", str(dist))

    reload_settings()
    return TestClient(create_app())


@pytest.fixture()
def ui(tmp_path, monkeypatch) -> TestClient:
    with _mk_client(tmp_path, monkeypatch, with_dist=True) as c:
        yield c


def test_root_serves_index_html(ui: TestClient) -> None:
    r = ui.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "<title>UI</title>" in r.text


def test_static_asset_is_served(ui: TestClient) -> None:
    r = ui.get("/assets/app.js")
    assert r.status_code == 200
    assert r.text == "console.log(1)"


@pytest.mark.parametrize("path", ["/records/abc123", "/search", "/deep/nested/route"])
def test_spa_fallback_returns_index(ui: TestClient, path: str) -> None:
    r = ui.get(path)
    assert r.status_code == 200
    assert "<title>UI</title>" in r.text


@pytest.mark.parametrize(
    "path",
    ["/api/v1/does-not-exist", "/api/nope", "/docs/nope", "/openapi.json/x"],
)
def test_backend_prefixes_never_fall_back_to_spa(ui: TestClient, path: str) -> None:
    """接口路径写错必须 404。回退成网页会让前端拿到 HTML 当 JSON 解析，排查起来极其痛苦。"""
    r = ui.get(path)
    assert r.status_code == 404
    assert "<title>UI</title>" not in r.text


def test_api_still_works_with_webui_mounted(ui: TestClient) -> None:
    assert ui.get("/api/v1/health").json()["status"] == "ok"


def test_directory_traversal_is_blocked(ui: TestClient) -> None:
    r = ui.get("/..%2f..%2frequirements.txt")
    # 要么 404，要么回退到 index.html，绝不能吐出 dist 之外的文件内容
    assert r.status_code in (200, 404)
    assert "fastapi" not in r.text.lower()


def test_without_dist_root_returns_self_description(tmp_path, monkeypatch) -> None:
    with _mk_client(tmp_path, monkeypatch, with_dist=False) as c:
        r = c.get("/")
        assert r.status_code == 200
        body = r.json()
        assert body["app"] == "SolveBase"
        assert "webui" in body
