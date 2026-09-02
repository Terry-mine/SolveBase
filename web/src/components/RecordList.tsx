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

interface Props {
  items: RecordItem[]
  selectedId: string | null
  vocab: Vocabulary | null
  onSelect: (id: string) => void
}

export function RecordList({ items, selectedId, vocab, onSelect }: Props) {
  if (items.length === 0) {
    return (
      <div className="p-8 text-center text-sm text-muted-foreground">
        还没有记录。用左边的速记框粘一段报错试试。
      </div>
    )
  }

  return (
    <div className="divide-y">
      {items.map((item) => {
        const Icon = TYPE_ICON[item.record_type as keyof typeof TYPE_ICON] ?? FileText
        const needsWork = item.missing.length > 0
        return (
          <button
            key={item.id}
            onClick={() => onSelect(item.id)}
            className={cn(
              "w-full px-4 py-3 text-left transition-colors",
              selectedId === item.id ? "bg-secondary" : "hover:bg-accent/60",
            )}
          >
            <div className="flex items-start gap-2">
              <Icon className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">{item.title}</div>

                <div className="mt-1.5 flex flex-wrap items-center gap-1">
                  <Badge variant="outline" className="font-normal">
                    {typeLabel(vocab, item.record_type)}
                  </Badge>
                  {item.category && (
                    <Badge variant="info" className="font-normal">
                      {categoryLabel(vocab, item.record_type, item.category)}
                    </Badge>
                  )}
                  <Badge variant={statusTone(item.status)} className="font-normal">
                    {statusLabel(vocab, item.record_type, item.status)}
                  </Badge>
                  {needsWork && (
                    <Badge variant="warning" className="font-normal">
                      待补全 {item.missing.length}
                    </Badge>
                  )}
                </div>

                <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                  {item.project && <span className="truncate">{item.project}</span>}
                  <span className="ml-auto shrink-0">{formatTime(item.updated_at)}</span>
                </div>
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}
