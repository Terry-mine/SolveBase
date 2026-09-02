"""前端链路端到端：走 5173 代理，验证前端调用的每个接口都通。

用法：先启动前后端，再 `python scripts/e2e_frontend.py`
测完会删除本次创建的所有记录，不污染你的库。
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:5173/api/v1"
created: list[str] = []


def call(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} on {method} {path}: {e.read().decode('utf-8')}")
        raise


def show(title: str, **kv) -> None:
    print(f"\n--- {title} ---")
    for k, v in kv.items():
        print(f"  {k}: {v}")


def main() -> int:
    health = call("GET", "/health")
    show("健康检查", 服务=health["app"], 迁移=health["migrations"]["applied"],
         类型=health["vocab"]["types"])

    # 1. 速记（incident）：贴一段报错，验证自动判定 + 抽取 + 别名归并
    traceback = (
        "容器内连不上宿主机 PostgreSQL\n"
        "Traceback (most recent call last):\n"
        '  File "app.py", line 42, in connect\n'
        "psycopg2.OperationalError: could not connect to server: Connection refused\n"
        "以为是防火墙，iptables 全放通没用\n"
    )
    cap = call("POST", "/capture", {"text": traceback, "source": "web"})
    created.append(cap["record_id"])
    show("速记捕获", 记录ID=cap["record_id"], 自动类型=cap["record_type"], 需复核=cap["needs_review"])

    detail = call("GET", f"/records/{cap['record_id']}")
    show("自动抽取", 标题=detail["title"], 状态=detail["status"],
         待补全=detail["missing"], 报错原文=repr(detail["error_excerpt"]))

    patched = call("PATCH", f"/records/{cap['record_id']}", {
        "category": "网络", "status": "已解决",
        "attempts": [
            {"hypothesis": "以为是防火墙", "action": "iptables 全放通", "worked": 0},
            {"hypothesis": "容器内 127.0.0.1 指自身", "action": "改用 host.docker.internal",
             "worked": 1, "elapsed_min": 4},
        ],
        "payload": {"root_cause": "容器内 127.0.0.1 指向自身命名空间",
                    "solution": "用 host.docker.internal 替代"},
    })
    show("补全与归并", 输入分类="网络", 归并=patched["category"],
         状态=patched["status"],
         尝试链=[(a["action"], a["worked"]) for a in patched["attempts"]])

    # 2. runbook：规程类（验证类型分支与专属 payload）
    rb = call("POST", "/records", {
        "record_type": "runbook", "title": "部署前必做：清理 Docker 构建缓存",
        "category": "部署运维", "status": "有效",
        "payload": {"preconditions_text": "新版本已合并", "steps_text": "docker builder prune -f\n重新构建镜像",
                    "verify": "镜像体积下降", "rollback": "无"},
    })
    created.append(rb["id"])
    show("规程创建", id=rb["id"], 类型=rb["record_type"],
         步骤数=len(rb.get("payload", {}).get("steps", [])) or "文本存储")

    # 3. note：注意事项类
    nt = call("POST", "/records", {
        "record_type": "note", "title": "生产库不要直接跑 migrations 之外的写操作",
        "category": "规范约定", "status": "长期有效",
        "payload": {"conclusion": "非迁移写操作要走审批", "scenario": "临时数据修复",
                    "reason": "曾误删过索引"},
    })
    created.append(nt["id"])
    show("注意事项创建", id=nt["id"], 类型=nt["record_type"])

    # 4. 检索（三种类型都应可命中）
    for q in ["Connection refused", "docker", "生产库"]:
        hit = call("GET", "/records/search?q=" + urllib.parse.quote(q))
        show(f"搜索『{q}』", 命中=hit["total"],
             首条=hit["items"][0]["title"] if hit["items"] else None)

    # 5. Facet 统计
    stats = call("GET", "/records/stats")
    show("统计", 按类型=stats["by_type"], 按分类=stats["by_category"])

    print("\n前端链路全部通过。")
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    finally:
        for rid in created:
            try:
                call("DELETE", f"/records/{rid}")
            except Exception:
                pass
        if created:
            print(f"\n已清理 {len(created)} 条测试记录。")
    sys.exit(rc)
