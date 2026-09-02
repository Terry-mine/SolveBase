"""初始结构。

设计要点（决定了后面好不好改）：

1. 三种记录类型共用一个 records 表，类型专属内容放 payload_json。
   加一种新记录类型不需要改表结构，只要往 config/vocab.yaml 加一项。
2. record_type / category 故意不加 SQL CHECK 约束。
   约束写在 domain 层（由词表驱动），改词表不用改表结构。
3. 同步字段（rev / device_id / updated_at / deleted_at / dirty / schema_ver）
   从第一版就建好。事后补这些字段需要全表迁移 + 重写所有写入路径。
4. 删除一律软删（deleted_at），同步时靠 tombstone 传播。
5. 全文索引用独立的 FTS5 表而不是外部内容表，
   这样「改完词表一键重建索引」就是一次 DELETE + INSERT，不用维护触发器。

本文件是历史，永不修改。要改结构请新建 002_xxx.py。
"""

VERSION = 1
DESCRIPTION = "初始结构：records / attempts / snippets / relations / embeddings / jobs / corrections / vocab / sync_state"

UP = """
-- ── 主表：三种记录类型共用 ──────────────────────────────────────
CREATE TABLE records (
    id            TEXT PRIMARY KEY,          -- UUIDv7，时间有序
    record_type   TEXT NOT NULL,             -- incident | runbook | note（由词表驱动）
    title         TEXT NOT NULL,
    status        TEXT NOT NULL,             -- draft + 各类型专属状态

    -- 分类三维
    category      TEXT,                      -- 闭集词表，取值域由 record_type 决定
    project       TEXT,                      -- 单值，归属
    systems_json  TEXT NOT NULL DEFAULT '[]',-- 多值：Docker / PostgreSQL / ...
    tags_json     TEXT NOT NULL DEFAULT '[]',

    -- 检索
    search_text   TEXT NOT NULL DEFAULT '',  -- 归一化后的可检索文本
    error_excerpt TEXT,                      -- 报错原文，永不改写
    error_fp      TEXT,                      -- 归一化指纹（P2 启用）
    payload_json  TEXT NOT NULL DEFAULT '{}',-- 类型专属内容
    confidence    REAL,                      -- LLM 规整置信度
    missing_json  TEXT NOT NULL DEFAULT '[]',-- 待补全字段

    -- 同步与版本（第一版就有）
    rev           INTEGER NOT NULL DEFAULT 1,
    device_id     TEXT NOT NULL,
    updated_at    INTEGER NOT NULL,
    deleted_at    INTEGER,                   -- 软删，tombstone
    dirty         INTEGER NOT NULL DEFAULT 1,-- 1 = 待同步
    schema_ver    INTEGER NOT NULL DEFAULT 1,

    hit_count     INTEGER NOT NULL DEFAULT 0,
    created_at    INTEGER NOT NULL
);

CREATE INDEX idx_records_type      ON records(record_type);
CREATE INDEX idx_records_category  ON records(category);
CREATE INDEX idx_records_project   ON records(project);
CREATE INDEX idx_records_updated   ON records(updated_at);
CREATE INDEX idx_records_created   ON records(created_at);
CREATE INDEX idx_records_deleted   ON records(deleted_at);
CREATE INDEX idx_records_fp        ON records(error_fp) WHERE error_fp IS NOT NULL;
CREATE INDEX idx_records_dirty     ON records(dirty) WHERE dirty = 1;

-- ── 尝试链：incident 的灵魂字段 ─────────────────────────────────
CREATE TABLE attempts (
    id          TEXT PRIMARY KEY,
    record_id   TEXT NOT NULL REFERENCES records(id) ON DELETE CASCADE,
    seq         INTEGER NOT NULL,
    hypothesis  TEXT,     -- 当时的假设
    action      TEXT,     -- 做了什么
    observation TEXT,     -- 观察到什么
    worked      INTEGER NOT NULL DEFAULT 0,  -- 1 奏效 / 0 无效 / -1 恶化
    elapsed_min INTEGER
);
CREATE INDEX idx_attempts_record ON attempts(record_id, seq);

-- ── 可复用片段 ─────────────────────────────────────────────────
CREATE TABLE snippets (
    id         TEXT PRIMARY KEY,
    record_id  TEXT NOT NULL REFERENCES records(id) ON DELETE CASCADE,
    kind       TEXT,      -- command | code | config | sql
    lang       TEXT,
    body       TEXT NOT NULL,
    note       TEXT,
    copy_count INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_snippets_record ON snippets(record_id);

-- ── 关联图谱 ───────────────────────────────────────────────────
CREATE TABLE relations (
    src   TEXT NOT NULL,
    dst   TEXT NOT NULL,
    rel   TEXT NOT NULL,  -- similar|duplicate|supersedes|caused_by|related_runbook
    score REAL,
    PRIMARY KEY (src, dst, rel)
);
CREATE INDEX idx_relations_src ON relations(src, rel);
CREATE INDEX idx_relations_dst ON relations(dst, rel);

-- ── 向量：多字段（检索侧 / 解法侧）─────────────────────────────
CREATE TABLE embeddings (
    record_id TEXT NOT NULL,
    field     TEXT NOT NULL,   -- search | solution
    model     TEXT NOT NULL,
    dim       INTEGER NOT NULL,
    vec       BLOB NOT NULL,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (record_id, field, model)
);

-- ── 流水线任务 ─────────────────────────────────────────────────
CREATE TABLE ingest_jobs (
    id         TEXT PRIMARY KEY,
    record_id  TEXT REFERENCES records(id) ON DELETE SET NULL,
    raw_text   TEXT,
    source     TEXT,          -- web | cli | import
    stage      TEXT NOT NULL, -- raw | normalized | enriched | linked | done | failed
    result_json TEXT,
    error      TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE INDEX idx_jobs_stage ON ingest_jobs(stage);

-- ── 纠偏闭环：人工修改回灌成 few-shot 样本 ──────────────────────
CREATE TABLE corrections (
    id          TEXT PRIMARY KEY,
    record_id   TEXT REFERENCES records(id) ON DELETE CASCADE,
    field       TEXT NOT NULL,
    llm_value   TEXT,
    human_value TEXT,
    created_at  INTEGER NOT NULL
);
CREATE INDEX idx_corrections_field ON corrections(field);

-- ── 受控词表（由 config/vocab.yaml 灌入，用于同义词归并）────────
CREATE TABLE vocab (
    kind        TEXT NOT NULL,  -- category | status
    type_key    TEXT NOT NULL,  -- incident | runbook | note | *
    code        TEXT NOT NULL,
    label       TEXT NOT NULL,
    aliases_json TEXT NOT NULL DEFAULT '[]',
    deprecated  INTEGER NOT NULL DEFAULT 0,
    use_count   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (kind, type_key, code)
);

-- ── 同步状态 ───────────────────────────────────────────────────
CREATE TABLE sync_state (
    peer           TEXT PRIMARY KEY,
    last_pulled_at INTEGER NOT NULL DEFAULT 0,
    last_pushed_at INTEGER NOT NULL DEFAULT 0,
    last_error     TEXT
);

-- ── 全文索引（独立表，可整体重建）────────────────────────────────
-- trigram 分词器对中文子串检索友好；代价是查询词需 >= 3 个字符，
-- 更短的查询由 repository 层回退到 LIKE。
CREATE VIRTUAL TABLE records_fts USING fts5(
    record_id     UNINDEXED,
    title,
    search_text,
    error_excerpt,
    tokenize='trigram'
);
"""


def up(conn) -> None:
    conn.executescript(UP)
