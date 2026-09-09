import { FileText, ListChecks, StickyNote } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { categoryLabel, statusLabel, statusTone, typeLabel } from "@/lib/labels"
import { cn, formatTime } from "@/lib/utils"
import type { RecordItem, Vocabulary } from "@/types"

const TYPE_ICON = {
  incident: FileText,
  runbook: ListChecks,
  note: StickyNote,
} as const

const TONE_BAR: Record<string, string> = {
  success: "tone-success",
  warning: "tone-warning",
  destructive: "tone-destructive",
  secondary: "tone-neutral",
}
const TONE_DOT: Record<string, string> = {
  success: "dot-success",
  warning: "dot-warning",
  destructive: "dot-destructive",
  secondary: "dot-neutral",
}

interface Props {
  items: RecordItem[]
  selectedId: string | null
  vocab: Vocabulary | null
  onSelect: (id: string) => void
}

export function RecordList({ items, selectedId, vocab, onSelect }: Props) {
  if (items.length === 0) {
    return (
      <div className="px-6 py-16 text-center">
        <p className="text-sm text-muted-foreground">还没有记录</p>
        <p className="mt-1 text-[11px] text-muted-foreground/70">
          用左下角速记框粘一段报错试试
        </p>
      </div>
    )
  }

  return (
    <div className="stagger divide-y divide-rule">
      {items.map((item) => {
        const Icon = TYPE_ICON[item.record_type as keyof typeof TYPE_ICON] ?? FileText
        const tone = statusTone(item.status)
        const selected = selectedId === item.id
        const needsWork = item.missing.length > 0

        return (
          <button
            key={item.id}
            onClick={() => onSelect(item.id)}
            className={cn(
              "lift group relative block w-full py-2.5 pl-5 pr-4 text-left",
              selected
                ? "bg-white/32 bg-gradient-to-br from-ledger/[0.08] via-ledger/[0.04] to-transparent"
                : "hover:bg-white/28",
            )}
          >
            {/* 状态色条 */}
            <span
              className={cn(
                "absolute inset-y-0 left-0 transition-all",
                TONE_BAR[tone],
                selected ? "w-1 shadow-[0_0_8px_currentColor]" : "w-[3px]",
              )}
            />

            {/* 选中态右侧的箭头标记 */}
            {selected && (
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-ledger">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </span>
            )}

            <div className="relative flex items-start gap-2">
              <Icon
                className={cn(
                  "mt-[3px] h-3.5 w-3.5 shrink-0 transition-transform group-hover:scale-110",
                  selected ? "text-ledger" : "text-muted-foreground/70",
                )}
              />

              <div className="min-w-0 flex-1">
                <div
                  className={cn(
                    "truncate text-sm leading-6",
                    selected ? "font-bold text-ledger" : "font-medium text-ink",
                  )}
                >
                  {item.title}
                </div>

                <div className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] leading-4">
                  <span className="text-muted-foreground">
                    {typeLabel(vocab, item.record_type)}
                  </span>

                  {item.category && (
                    <Badge variant="outline">
                      {categoryLabel(vocab, item.record_type, item.category)}
                    </Badge>
                  )}

                  <span className={cn("flex items-center gap-1", TONE_DOT[tone])}>
                    <span className="text-[9px] leading-none">●</span>
                    {statusLabel(vocab, item.record_type, item.status)}
                  </span>

                  {needsWork && (
                    <Badge variant="destructive">待补全 {item.missing.length}</Badge>
                  )}
                </div>

                <div className="mt-1 flex items-baseline gap-2 text-[11px] leading-4 text-muted-foreground">
                  <span className="truncate">{item.project || "—"}</span>
                  <span className="data-num ml-auto shrink-0 tabular-nums">
                    {formatTime(item.updated_at)}
                  </span>
                </div>
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}