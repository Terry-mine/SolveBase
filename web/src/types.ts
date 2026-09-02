/** 与后端 domain/models.py 对应的前端契约。
 *  改后端模型时同步这里，是唯一的耦合点。 */

export type RecordType = "incident" | "runbook" | "note"

export interface Attempt {
  id?: string
  seq?: number
  hypothesis: string | null
  action: string | null
  observation: string | null
  worked: number // 1 奏效 / 0 无效 / -1 恶化
  elapsed_min: number | null
}

export interface Snippet {
  id?: string
  kind: string | null
  lang: string | null
  body: string
  note: string | null
  copy_count?: number
}

export interface RecordItem {
  id: string
  record_type: string
  title: string
  status: string
  category: string | null
  project: string | null
  systems: string[]
  tags: string[]
  search_text: string
  error_excerpt: string | null
  error_fp: string | null
  payload: Record<string, unknown>
  confidence: number | null
  missing: string[]
  attempts: Attempt[]
  snippets: Snippet[]
  rev: number
  device_id: string
  dirty: number
  schema_ver: number
  hit_count: number
  created_at: number
  updated_at: number
  deleted_at: number | null
}

export interface Page<T> {
  items: T[]
  total: number
  offset: number
  limit: number
}

export interface VocabOption {
  code: string
  label: string
  desc?: string
}

export interface VocabType {
  key: string
  label: string
  desc: string
  statuses: VocabOption[]
  categories: VocabOption[]
}

export interface Vocabulary {
  version: number
  common_statuses: VocabOption[]
  types: VocabType[]
  issues: { level: string; message: string }[]
}

export interface ListParams {
  record_type?: string
  category?: string
  project?: string
  status?: string
  system?: string
  tag?: string
  q?: string
  order?: string
  limit?: number
  offset?: number
}

export interface StatsBucket {
  key: string | null
  count: number
}
