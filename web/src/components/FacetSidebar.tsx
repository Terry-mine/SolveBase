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
    <div className="relative border-t border-rule px-3 py-2.5">
      <div className="mb-1.5 flex items-center gap-1.5">
        <span className="h-1 w-1 rounded-full bg-ledger" />
        <span className="text-[11px] font-bold leading-4 text-muted-foreground">
          {title}
        </span>
      </div>
      <div className="space-y-px">{children}</div>
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
        "relative flex w-full items-center justify-between rounded-sm py-1 pl-2.5 pr-2 text-left text-[13px] leading-5 transition-all duration-150",
        active
          ? "bg-gradient-to-r from-ledger/15 to-ledger/5 font-bold text-ledger-ink selection-glow"
          : "text-foreground/80 hover:bg-accent/70 hover:translate-x-0.5",
      )}
    >
      {active && (
        <span className="absolute inset-y-0.5 left-0 w-[2px] rounded-sm bg-ledger" />
      )}
      <span className="truncate">{label}</span>
      {count !== undefined && count > 0 && (
        <span
          className={cn(
            "data-num ml-2 shrink-0 rounded px-1 text-[10px] leading-4",
            active ? "bg-ledger/15 font-bold" : "text-muted-foreground",
          )}
        >
          {count}
        </span>
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
    <aside className="glass-strong relative flex w-64 shrink-0 flex-col overflow-hidden border-r">
      {children}

      {/* 极淡网格背景，仅下半部分 */}
      <div className="relative flex-1 overflow-y-auto">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 grid-bg opacity-40"
        />
        <div className="relative">
          <Group title="记录类型">
            <Option
              active={!activeType}
              onClick={() =>
                onChange({
                  ...filters,
                  record_type: undefined,
                  category: undefined,
                  status: undefined,
                })
              }
              label="全部"
              count={Object.values(counts.types).reduce((a, b) => a + b, 0)}
            />
            {vocab?.types.map((t) => (
              <Option
                key={t.key}
                active={activeType === t.key}
                onClick={() =>
                  onChange({
                    ...filters,
                    record_type: toggle(filters.record_type, t.key),
                    category: undefined,
                    status: undefined,
                  })
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
                    onClick={() =>
                      onChange({ ...filters, category: toggle(filters.category, c.code) })
                    }
                    label={c.label}
                  />
                ))}
              </Group>

              <Group title="状态">
                {statuses.map((s) => (
                  <Option
                    key={`${s.code}-${s.label}`}
                    active={filters.status === s.code}
                    onClick={() =>
                      onChange({ ...filters, status: toggle(filters.status, s.code) })
                    }
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
              onChange={(e) =>
                onChange({ ...filters, project: e.target.value || undefined })
              }
              placeholder="输入项目名过滤"
              className="h-7 w-full rounded-sm border border-white/45 bg-white/45 px-2 text-[11px] placeholder:text-muted-foreground/70 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            />
          </Group>

          {vocab?.issues && vocab.issues.length > 0 && (
            <div className="border-t border-rule px-3 py-2.5">
              <Badge variant="destructive" className="mb-1.5">
                词表提示
              </Badge>
              {vocab.issues.map((i, idx) => (
                <p key={idx} className="text-[11px] leading-4 text-muted-foreground">
                  {i.message}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}