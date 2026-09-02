import type { Vocabulary } from "@/types"

export function typeLabel(vocab: Vocabulary | null, key: string): string {
  return vocab?.types.find((t) => t.key === key)?.label ?? key
}

export function categoryLabel(vocab: Vocabulary | null, typeKey: string, code: string | null): string {
  if (!code) return ""
  const spec = vocab?.types.find((t) => t.key === typeKey)
  return spec?.categories.find((c) => c.code === code)?.label ?? code
}

export function statusLabel(vocab: Vocabulary | null, typeKey: string, code: string): string {
  const spec = vocab?.types.find((t) => t.key === typeKey)
  const own = spec?.statuses.find((s) => s.code === code)?.label
  if (own) return own
  return vocab?.common_statuses.find((s) => s.code === code)?.label ?? code
}

export function statusOptions(vocab: Vocabulary | null, typeKey: string) {
  const spec = vocab?.types.find((t) => t.key === typeKey)
  return [...(vocab?.common_statuses ?? []), ...(spec?.statuses ?? [])]
}

export function categoryOptions(vocab: Vocabulary | null, typeKey: string) {
  return vocab?.types.find((t) => t.key === typeKey)?.categories ?? []
}

/** 状态徽章配色：已解决绿、未解决/复发红、草稿灰 */
export function statusTone(code: string): "success" | "warning" | "destructive" | "secondary" {
  if (["solved", "active"].includes(code)) return "success"
  if (["regressed", "open", "deprecated", "outdated"].includes(code)) return "destructive"
  if (["workaround", "needs_update"].includes(code)) return "warning"
  return "secondary"
}
