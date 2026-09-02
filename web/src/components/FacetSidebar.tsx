import type { ListParams, Vocabulary } from "@/types"

import { Badge } from "@/components/ui/badge"
import { categoryOptions, statusOptions } from "@/lib/labels"
import { cn } from "@/lib/utils"

interface Props {
  vocab: Vocabulary | null
  filters: ListParams
  onChange: (next: ListParams) => void
  counts: { types: Record<string, number>; statuses: Record<string, number> }
  children?: React.ReactNode
}

function Group({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5 border-t px-4 py-3">
      <div className="text-xs font-medium text-muted-foreground">{title}</div>
      <div className="space-y-0.5">{children}</div>
    </div>
  )
}

function Option({
  active,
  onClick,
  label,
  count,
}: {
  active: boolean
  onClick: () => void
  label: string
  count?: number
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex w-full items-center justify-between rounded px-2 py-1 text-left text-sm transition-colors",
        active ? "bg-secondary font-medium" : "hover:bg-accent",
      )}
    >
      <span className="truncate">{label}</span>
      {count !== undefined && count > 0 && (
        <span className="ml-2 shrink-0 text-xs text-muted-foreground">{count}</span>
      )}
    </button>
  )
}

function toggle<T>(current: T | undefined, value: T): T | undefined {
  return current === value ? undefined : value
}

export function FacetSidebar({ vocab, filters, onChange, counts, children }: Props) {
  const activeType = filters.record_type ?? ""
  const statuses = activeType ? statusOptions(vocab, activeType) : []
  const categories = activeType ? categoryOptions(vocab, activeType) : []

  return (
    <aside className="flex w-64 shrink-0 flex-col overflow-y-auto border-r">
      {children}
      <Group title="记录类型">
        <Option
          active={!activeType}
          onClick={() => onChange({ ...filters, record_type: undefined, category: undefined, status: undefined })}
          label="全部"
        />
        {vocab?.types.map((t) => (
          <Option
            key={t.key}
            active={activeType === t.key}
            onClick={() =>
              onChange({ ...filters, record_type: toggle(filters.record_type, t.key), category: undefined, status: undefined })
            }
            label={t.label}
            count={counts.types[t.key]}
          />
        ))}
      </Group>

      {activeType && (
        <>
          <Group title="类别">
            {categories.map((c) => (
              <Option
                key={c.code}
                active={filters.category === c.code}
                onClick={() => onChange({ ...filters, category: toggle(filters.category, c.code) })}
                label={c.label}
              />
            ))}
          </Group>

          <Group title="状态">
            {statuses.map((s) => (
              <Option
                key={`${s.code}-${s.label}`}
                active={filters.status === s.code}
                onClick={() => onChange({ ...filters, status: toggle(filters.status, s.code) })}
                label={s.label}
                count={counts.statuses[s.code]}
              />
            ))}
          </Group>
        </>
      )}

      <Group title="项目">
        <input
          value={filters.project ?? ""}
          onChange={(e) => onChange({ ...filters, project: e.target.value || undefined })}
          placeholder="输入项目名过滤"
          className="h-8 w-full rounded-md border border-input bg-transparent px-2 text-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        />
      </Group>

      {vocab?.issues && vocab.issues.length > 0 && (
        <div className="border-t px-4 py-3">
          <Badge variant="warning" className="mb-1">
            词表提示
          </Badge>
          {vocab.issues.map((i, idx) => (
            <p key={idx} className="text-xs text-muted-foreground">
              {i.message}
            </p>
          ))}
        </div>
      )}
    </aside>
  )
}
