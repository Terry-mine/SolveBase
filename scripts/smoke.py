"""端到端冒烟脚本：对着真实运行的 HTTP 服务跑一遍主流程。

用法：先 `python -m backend.cli serve`，再 `python scripts/smoke.py`
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8787/api/v1"


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
         类型=health["vocab"]["types"], LLM已启用=health["providers"]["enabled"]["llm"])

    traceback = (
        "容器内连不上宿主机 PostgreSQL\n"
        "Traceback (most recent call last):\n"
        '  File "app.py", line 42, in connect\n'
        "psycopg2.OperationalError: could not connect to server: Connection refused\n"
        "以为是防火墙，iptables 全放通没用\n"
    )
    cap = call("POST", "/capture", {"text": traceback, "source": "web"})
    rid = cap["record_id"]
    show("速记捕获", 记录ID=rid, 自动判定类型=cap["record_type"], 待人工确认=cap["needs_review"])

    detail = call("GET", f"/records/{rid}")
    show("自动抽取结果", 标题=detail["title"], 状态=detail["status"],
         待补全=detail["missing"], 报错原文=repr(detail["error_excerpt"]))

    patched = call("PATCH", f"/records/{rid}", {
        "category": "网络",
        "status": "已解决",
        "attempts": [
            {"hypothesis": "以为是防火墙", "action": "iptables 全放通", "worked": 0},
            {"hypothesis": "容器内 127.0.0.1 指自身", "action": "改用 host.docker.internal",
             "worked": 1, "elapsed_min": 4},
        ],
        "payload": {"root_cause": "容器内 127.0.0.1 指向自身命名空间",
                    "solution": "用 host.docker.internal 替代"},
    })
    show("补全与归并", 输入分类="网络", 归并结果=patched["category"],
         状态=patched["status"],
         尝试链=[(a["action"], a["worked"]) for a in patched["attempts"]],
         根因=patched["payload"]["root_cause"])

    hit = call("GET", "/records/search?q=" + urllib.parse.quote("Connection refused"))
    show("关键词检索", 命中数=hit["total"], 首条=hit["items"][0]["title"] if hit["items"] else None)

    vocab = call("GET", "/vocab")
    incident = next(t for t in vocab["types"] if t["key"] == "incident")
    show("词表", 版本=vocab["version"], incident分类数=len(incident["categories"]),
         词表问题=vocab["issues"])

    syncst = call("GET", "/sync/status")
    show("同步", provider=syncst["provider"], 已启用=syncst["enabled"])

    stats = call("GET", "/records/stats")
    show("统计", 按类型=stats["by_type"], 按分类=stats["by_category"])

    print("\n全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
