"""端到端冒烟测试。

这些用例锁住的是"契约"而不是实现细节 ——
以后换 provider、换存储、改词表，只要这些测试还是绿的，就没改坏。
"""

from __future__ import annotations

import base64

import pytest
from fastapi.testclient import TestClient

from backend.core.config import reload_settings
from backend.main import create_app

TRACEBACK = """Traceback (most recent call last):
  File "app.py", line 42, in connect
    conn = psycopg2.connect(host="127.0.0.1", port=5432)
psycopg2.OperationalError: could not connect to server: Connection refused
"""


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("SOLVEBASE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SOLVEBASE_DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("SOLVEBASE_ASSETS_DIR", str(tmp_path / "assets"))
    reload_settings()
    with TestClient(create_app()) as c:
        yield c


def test_health_reports_migrations_and_providers(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["migrations"]["latest"] == 1
    assert body["vocab"]["types"] == ["incident", "runbook", "note"]
    assert body["providers"]["enabled"] == {
        "llm": False, "embedding": False, "reranker": False, "sync": False,
    }


def test_capture_creates_incident_from_traceback(client: TestClient) -> None:
    r = client.post(
        "/api/v1/capture",
        json={
            "text": TRACEBACK,
            "source": "web",
            "title": "容器内连不上宿主机 PostgreSQL",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["record_type"] == "incident"
    assert body["needs_review"] is True

    detail = client.get(f"/api/v1/records/{body['record_id']}").json()
    assert detail["status"] == "draft"
    assert "Connection refused" in (detail["error_excerpt"] or "")
    assert "category" in detail["missing"]


def test_capture_guesses_runbook_from_intent(client: TestClient) -> None:
    r = client.post(
        "/api/v1/capture",
        json={
            "text": "生产环境发版的完整步骤有哪些，需要先做什么检查",
            "source": "web",
            "title": "生产环境发版步骤",
        },
    )
    assert r.json()["record_type"] == "runbook"


def test_capture_requires_title(client: TestClient) -> None:
    """title 硬性必填：缺了要被挡住，而不是悄悄生成一个认不出的自动标题。"""
    r = client.post("/api/v1/capture", json={"text": "一段报错"})
    assert r.status_code == 400


def test_capture_keeps_image_assets(client: TestClient) -> None:
    """截图落盘后：元信息进 payload.images，字节留在磁盘，且不混进原始记录文本。"""
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    up = client.post("/api/v1/images", files={"file": ("shot.png", png, "image/png")})
    assert up.status_code == 201
    asset = up.json()
    assert asset["url"].startswith("/api/v1/images/")
    # OCR 还没接，但字段已经留好，接的时候不用改数据形状
    assert asset["ocr"]["status"] == "pending"

    # 落盘的图片能按 url 取回
    assert client.get(asset["url"]).status_code == 200

    r = client.post(
        "/api/v1/capture",
        json={
            "text": "粘贴了一张报错截图",
            "title": "登录报错截图",
            "images": [asset],
        },
    )
    assert r.status_code == 201
    detail = client.get(f"/api/v1/records/{r.json()['record_id']}").json()

    images = detail["payload"]["images"]
    assert len(images) == 1
    assert images[0]["filename"] == asset["filename"]
    # 图片是独立字段，不混进原始记录，也不影响标题
    assert asset["filename"] not in detail["search_text"]
    assert detail["title"] == "登录报错截图"


def test_category_alias_is_normalized(client: TestClient) -> None:
    created = client.post(
        "/api/v1/records",
        json={"record_type": "incident", "title": "容器内连不上宿主 PostgreSQL", "category": "依赖"},
    )
    assert created.status_code == 201
    assert created.json()["category"] == "DepsVersion"


@pytest.mark.parametrize("raw,expected", [
    ("已解决", "solved"),
    ("resolved", "solved"),
    ("搞定", "solved"),
    ("未解决", "open"),
    ("复发", "regressed"),
])
def test_status_label_and_alias_normalize_to_code(
    client: TestClient, raw: str, expected: str
) -> None:
    """状态必须收敛回 code。

    否则 LLM 输出 resolved、前端显示"已解决"，会和 solved 变成三个状态，统计直接散掉。
    """
    r = client.post(
        "/api/v1/records",
        json={"record_type": "incident", "title": "状态归一测试", "status": raw},
    )
    assert r.status_code == 201
    assert r.json()["status"] == expected


def test_unknown_category_is_left_empty_not_rejected(client: TestClient) -> None:
    created = client.post(
        "/api/v1/records",
        json={"record_type": "incident", "title": "一个还没归类的怪问题", "category": "玄学问题"},
    )
    assert created.status_code == 201
    assert created.json()["category"] is None


def test_unknown_record_type_is_rejected(client: TestClient) -> None:
    r = client.post("/api/v1/records", json={"record_type": "nope", "title": "x"})
    assert r.status_code == 400


def test_attempts_round_trip(client: TestClient) -> None:
    created = client.post(
        "/api/v1/records",
        json={
            "record_type": "incident",
            "title": "容器内连不上宿主 PostgreSQL",
            "attempts": [
                {"hypothesis": "以为是防火墙", "action": "iptables 全放通", "worked": 0},
                {"hypothesis": "容器里 127.0.0.1 指自身", "action": "改用 host.docker.internal", "worked": 1},
            ],
        },
    )
    rid = created.json()["id"]
    detail = client.get(f"/api/v1/records/{rid}").json()
    assert len(detail["attempts"]) == 2
    assert detail["attempts"][0]["worked"] == 0
    assert detail["attempts"][1]["worked"] == 1


def test_search_finds_record_by_keyword(client: TestClient) -> None:
    client.post(
        "/api/v1/records",
        json={"record_type": "incident", "title": "Nginx 502 排查", "search_text": "upstream prematurely closed connection"},
    )
    r = client.get("/api/v1/records/search", params={"q": "upstream"})
    assert r.status_code == 200
    assert any("Nginx 502" in i["title"] for i in r.json()["items"])


def test_short_query_falls_back_to_like(client: TestClient) -> None:
    """trigram 分词器不支持 <3 字符查询，必须回退到 LIKE 而不是报错。"""
    client.post("/api/v1/records", json={"record_type": "note", "title": "GC 调优注意", "search_text": "GC 停顿"})
    r = client.get("/api/v1/records/search", params={"q": "GC"})
    assert r.status_code == 200
    assert any("GC" in i["title"] for i in r.json()["items"])


def test_soft_delete_hides_from_list(client: TestClient) -> None:
    rid = client.post("/api/v1/records", json={"record_type": "note", "title": "待删除"}).json()["id"]
    assert client.get("/api/v1/records").json()["total"] == 1

    assert client.delete(f"/api/v1/records/{rid}").json()["deleted"] is True
    assert client.get("/api/v1/records").json()["total"] == 0
    assert client.get(f"/api/v1/records/{rid}").status_code == 404


def test_vocab_endpoint_exposes_all_types(client: TestClient) -> None:
    body = client.get("/api/v1/vocab").json()
    assert {t["key"] for t in body["types"]} == {"incident", "runbook", "note"}
    incident = next(t for t in body["types"] if t["key"] == "incident")
    assert len(incident["categories"]) == 16


def test_sync_is_disabled_at_p0(client: TestClient) -> None:
    body = client.get("/api/v1/sync/status").json()
    assert body["provider"] == "noop"
    assert body["enabled"] is False
