import { Plus, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import type { Attempt } from "@/types"

const WORKED_OPTIONS = [
  { value: 0, label: "无效", tone: "text-neutral-ink" },
  { value: 1, label: "奏效", tone: "text-pine-ink" },
  { value: -1, label: "恶化", tone: "text-seal-ink" },
] as const

/**
 * 尝试时间线。
 *
 * 这是整个系统区别于普通笔记的地方：「我试过什么没用」比「正确答案」更值钱，
 * 所以失败尝试必须可见（灰显），而不是被折叠掉。
 */
export function AttemptsEditor({
  attempts,
  onChange,
}: {
  attempts: Attempt[]
  onChange: (next: Attempt[]) => void
}) {
  function update(index: number, patch: Partial<Attempt>) {
    const next = attempts.map((a, i) => (i === index ? { ...a, ...patch } : a))
    onChange(next)
  }

  function remove(index: number) {
    onChange(attempts.filter((_, i) => i !== index).map((a, i) => ({ ...a, seq: i })))
  }

  function add() {
    onChange([
      ...attempts,
      { hypothesis: "", action: "", observation: "", worked: 0, elapsed_min: null, seq: attempts.length },
    ])
  }

  return (
    <div className="space-y-3">
      {attempts.length === 0 && (
        <p className="text-xs text-muted-foreground">
          还没有记录尝试过程。加一条「以为是 X，做了 Y，结果 Z」—— 这才是这条记录最值钱的部分。
        </p>
      )}

      {attempts.map((a, index) => {
        const failed = a.worked !== 1
        return (
          <div key={index} className="relative pl-7">
            {/* 时间线节点与连线 */}
            <div
              className={cn(
                "absolute left-0 top-1 flex h-5 w-5 items-center justify-center rounded-full border text-[10px]",
                a.worked === 1
                  ? "border-pine/40 bg-pine/15 text-pine-ink shadow-[0_0_8px_-2px_hsl(var(--pine)/0.5)]"
                  : a.worked === -1
                    ? "border-seal/40 bg-seal/15 text-seal-ink shadow-[0_0_8px_-2px_hsl(var(--seal)/0.5)]"
                    : "border-rule bg-muted text-muted-foreground",
              )}
            >
              {a.worked === 1 ? "✓" : a.worked === -1 ? "✕" : "·"}
            </div>
            {index < attempts.length - 1 && (
              <div className="absolute left-[10px] top-7 h-[calc(100%-1rem)] w-px bg-gradient-to-b from-rule to-transparent" />
            )}

            <div className={cn("space-y-1.5", failed && "opacity-70")}>
              <Input
                value={a.hypothesis ?? ""}
                onChange={(e) => update(index, { hypothesis: e.target.value })}
                placeholder="当时的假设"
                className={cn("h-7 text-xs", failed && "line-through decoration-muted-foreground/40")}
              />
              <Input
                value={a.action ?? ""}
                onChange={(e) => update(index, { action: e.target.value })}
                placeholder="做了什么"
                className="h-7 text-xs"
              />
              <Textarea
                value={a.observation ?? ""}
                onChange={(e) => update(index, { observation: e.target.value })}
                placeholder="观察到什么"
                className="min-h-[48px] text-xs"
              />

              <div className="flex items-center gap-1">
                {WORKED_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => update(index, { worked: opt.value })}
                    className={cn(
                      "rounded border px-2 py-0.5 text-xs transition-colors",
                      a.worked === opt.value
                        ? cn("border-current font-medium", opt.tone)
                        : "border-border text-muted-foreground hover:bg-accent",
                    )}
                  >
                    {opt.label}
                  </button>
                ))}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => remove(index)}
                  className="ml-auto h-6 px-2 text-xs text-muted-foreground"
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>
        )
      })}

      <Button variant="outline" size="sm" onClick={add} className="w-full text-xs">
        <Plus className="h-3 w-3" />
        加一条尝试
      </Button>
    </div>
  )
}
