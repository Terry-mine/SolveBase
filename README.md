# SolveBase

解题过程自动规整 + 极速检索。当前进度：**P0 后端 + 前端已完成，可直接录入使用；未接 LLM，未做云端同步**。

---

## 日常启动（双击就行）

根目录下有 6 个脚本，**日常只会用到前两个**：

| 双击这个 | 干什么 | 什么时候用 |
|---|---|---|
| **start.bat** | 启动并自动打开浏览器 → http://127.0.0.1:8787 | 每天记录时 |
| **stop.bat** | 停掉全部服务 | 不用了 / 要重启 |
| build.bat | 重新构建前端 | 改过 `web/src` 代码之后 |
| start-dev.bat | 开发模式（后端 8787 + vite 5173 热更新） | 只在改前端代码时 |
| install-autostart.bat | 注册开机自启 | 一次就够 |
| uninstall-autostart.bat | 取消开机自启 | 想关掉时 |

**单进程模式**：`start.bat` 只拉起一个 Python 进程（`pythonw.exe scripts/serve_bg.py`），
后端同时托管 `web/dist` 的界面。所以运行期**不需要 Node**、**只占一个端口 8787**、
**不留黑窗口**。浏览器直接开 http://127.0.0.1:8787。

启动失败或页面打不开时，第一件事是看 **`logs/server.log`**（无窗口模式下这是唯一的日志出口，
超过 2MB 自动轮转成 `server.log.1`）。

开机自启的做法是往「启动」文件夹丢一个静默启动器
（`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SolveBase.vbs`）——
用户级、不需要管理员、不碰注册表、删掉文件即失效。自启时不弹黑窗口、不自动开浏览器，
把 http://127.0.0.1:8787 存成书签或浏览器主页即可。

### 手动命令（脚本背后就是这些）

```bash
# 首次：建环境
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt

# 启动（建库/迁移/灌词表会自动完成，不用手动敲）
python -m backend.cli serve             # → http://127.0.0.1:8787 界面 + API
python -m backend.cli serve --reload    # 改后端代码时

# 构建前端（产物进 web/dist，由后端托管）
cd web && npm install && npm run build
```

其他命令：

```bash
python -m backend.cli info      # 看库、迁移、provider、词表问题
python -m backend.cli audit     # 只检查词表
python -m backend.cli reindex   # 重建全文索引
python -m pytest -q             # 跑全部测试
```

### 两种运行形态

| | 单进程（默认） | 开发模式 |
|---|---|---|
| 启动 | `start.bat` | `start-dev.bat` |
| 地址 | 8787（界面 + API） | 5173 界面 / 8787 API |
| 前端来源 | `web/dist` 构建产物 | vite 内存编译，改即刷新 |
| 需要 Node | 否 | 是 |
| 改前端后 | 要 `build.bat` + 重启 | 自动热更新 |

想关掉后端托管界面（比如以后前端交给 nginx），在 `.env` 里写 `SOLVEBASE_SERVE_WEBUI=false` 即可，
后端退回纯 API，根路径返回自述 JSON。

---

## 目录结构与分层规则

```
config/vocab.yaml     受控词表（分类体系的唯一事实来源）
backend/
  core/               配置、ID、时间。不依赖任何业务
  domain/             领域模型与规则。不依赖框架、不依赖数据库
  ports/              抽象接口（LLM / Embedding / Reranker / Sync）
  adapters/           接口的具体实现，全部可插拔
  services/           业务编排（捕获、分类、provider 装配）
  db/
    migrations/       版本化迁移
    repositories/     唯一允许写 SQL 的地方
  api/                FastAPI 路由，只做参数校验与响应组装
    webui.py          托管 web/dist（单进程模式的关键），可用配置关掉
  main.py             全项目唯一组装点

web/                  React + Vite + Tailwind 前端
  src/components/ui/   shadcn 风格基础组件（button/input/dialog/select...）
  src/components/      业务组件（CaptureBox/RecordList/RecordDetail/FacetSidebar/AttemptsEditor）
  src/lib/             api 客户端、标签映射、工具函数
  src/hooks/          useVocabulary 等
  vite.config.ts      /api 代理到后端 8787，开发免跨域
  dist/               构建产物，由后端直接托管

scripts/serve_bg.py   无窗口后台启动入口（把日志接到 logs/server.log）
logs/server.log       运行日志，排查第一站

start.bat             日常启动（单进程，自动开浏览器）
stop.bat              停止全部服务
build.bat             重新构建前端
start-dev.bat         开发模式（后端 + vite 热更新）
start.vbs             静默启动器（无黑窗口，供自启使用）
install-autostart.bat / uninstall-autostart.bat   开机自启的开关
```

依赖方向严格单向：`api → services → domain/ports → core`，`adapters → ports`。
**domain 层不许 import fastapi 或 sqlite3**，这条守住了，换框架换存储就都是局部改动。

---

## 六种常见改动，分别该动哪里

这张表就是"改一块不用动整体"的落地清单。

### 1. 改分类 / 加分类

只改 `config/vocab.yaml`，然后：

```bash
python -m backend.cli seed
```

前端下拉框从 `/api/v1/vocab` 取，不硬编码，刷新即生效。
**不要删除已有分类**，标 `deprecated: true` 即可 —— 老记录还要能正常显示。

### 2. 加数据库字段 / 新表

在 `backend/db/migrations/versions/` 下新建 `002_xxx.py`：

```python
VERSION = 2
DESCRIPTION = "加了 xxx 字段"

def up(conn):
    conn.executescript("ALTER TABLE records ADD COLUMN xxx TEXT")
```

然后 `python -m backend.cli migrate`。
**已应用的迁移文件永不修改**，这是多台机器库结构一致的前提。

### 3. 加一种记录类型

1. `config/vocab.yaml` 的 `types` 下加一项（label + statuses + categories）
2. `backend/domain/payloads.py` 里加一个 `@register("新类型")` 的校验函数
3. `python -m backend.cli seed`

不需要改表结构（payload 存在 `payload_json` 里），不需要改主流程。

### 4. 接真实 LLM / Embedding / Reranker

在 `backend/adapters/llm/` 下新建文件：

```python
from ...ports.llm import LLMProvider
from ...services.registry import register

@register("llm", "deepseek")
class DeepSeekLLM:
    name = "deepseek"
    def __init__(self, settings=None, **kwargs): ...
    def complete_json(self, *, system, user, schema=None, temperature=0.2) -> dict: ...
    def health(self) -> dict: ...
```

然后在 `backend/adapters/__init__.py` 加一行 import，
最后 `.env` 里设 `SOLVEBASE_LLM_PROVIDER=deepseek`。

业务代码一行都不用改 —— 它只认 `ports/llm.py` 里的协议。

### 5. 升级检索算法（P2）

改动集中在 `RecordRepository.search_ids()`，后续会替换为
「指纹 + BM25 + 向量 → RRF 融合 → rerank」。
路由 `/api/v1/records/search` 的签名和返回结构保持不变，前端不用动。

### 6. 启用同步（P4）

实现 `ports/sync.py` 里的 `SyncProvider`，用 `@register("sync", "bundle")` 登记即可。
`records` 表的同步字段（`rev` / `device_id` / `updated_at` / `deleted_at` / `dirty` / `schema_ver`）
和 `RecordRepository.changes_since()` / `dirty_ids()` / `mark_clean()` **从第一版就备好了**。

---

## 四条硬约束

1. **绝不通过同步 .db 文件实现多端同步。** SQLite 文件放进网盘同步目录会导致数据库损坏。
   必须走记录级 changeset（接口已在 `ports/sync.py` 定好）。
2. **已应用的迁移文件永不修改。** 要改结构就加新迁移。
3. **分类词表必须是闭集。** 让 LLM 自由发挥分类，三个月后同义词爆炸，统计和检索一起失效。
4. **domain / ports 层不许 import fastapi 或 sqlite3；SQL 只写在 db/ 目录。**
   前三条靠自觉，这条有测试兜着（见下）。

---

## 测试

```bash
python -m pytest -q
```

两组用例，保护的东西不一样：

- `tests/test_smoke.py` —— 保护**契约**。速记、类型判定、分类归并、状态归一、
  尝试链、检索、软删。以后换 provider、改词表，只要这些还是绿的就没改坏。
- `tests/test_architecture.py` —— 保护**分层**。adapter 是否满足端口协议、
  每个 kind 是否有 noop 兜底、迁移版本号是否唯一、domain 有没有偷偷依赖框架、
  SQL 有没有漏到 db/ 外面。这些红了说明有人在破坏可维护性。

另有 `scripts/smoke.py`：对着真实运行的 HTTP 服务跑一遍主流程，输出可读的检查结果。
先 `python -m backend.cli serve`，再 `python scripts/smoke.py`。

---

## P0 已完成 / 后续待办

| 阶段 | 内容 | 状态 |
|---|---|---|
| P0 | 工程骨架、版本化迁移、词表外部化、provider 抽象、CRUD + 全文检索 | ✅ 完成 |
| P0 | 前端（Inbox 速记 / 检索 / 三栏详情 / Facet 过滤） | ✅ 完成 |
| — | 手工填 30~50 条真实记录，作为 prompt 基准集 | ⬜ 待做 |
| P1 | 接 LLM 规整流水线 + staging 确认 + corrections 纠偏闭环 | ⬜ 待做 |
| P2 | 报错指纹 + 向量召回 + RRF 融合 + rerank | ⬜ 待做 |
| P3 | 统计视图、关联图谱、片段一键复制、批量重分类 | ⬜ 待做 |
| P4 | 同步：导出包 → 网盘目录自动导入 | ⬜ 待做 |

**注意顺序**：P1 开始前先攒够 30~50 条真实记录。没有基准集就无法判断 prompt 好坏，
也攒不出 few-shot 样本。先上自动化等于闭着眼睛调参。

## 日常怎么用

1. 双击 `start.bat`（或已注册开机自启，直接开浏览器）→ http://127.0.0.1:8787
2. 顶部速记框粘一段报错 / 粘贴内容回车 → 自动判定类型、抽取报错，进 Inbox 待补全
3. 点记录进详情页，补全分类 / 状态 / 尝试链 / 解法，保存即生效
4. 左侧 Facet 按 类型 / 项目 / 系统 / 分类 / 状态 过滤，顶部搜索框做全文检索（命中高亮）
5. **攒够 30~50 条真实记录后，再接 P1 的 LLM 自动规整** —— 没有基准集就没法判断 prompt 好坏

Swagger 页面 http://127.0.0.1:8787/docs 仍可用，适合调试和批量脚本。

另有 `scripts/e2e_frontend.py`：对着 5173 端口（前端→代理→后端完整链路）跑一遍主流程，
测完自动清理测试记录。先 `start-dev.bat` 起开发模式，再 `python scripts/e2e_frontend.py`。

`scripts/smoke.py` 是对 8787 的端到端检查，**注意它不清理数据**，跑完会留一条
「容器内连不上宿主机 PostgreSQL」的示例记录，看到了手动删掉即可。
