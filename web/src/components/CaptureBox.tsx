import { useState } from "react"
import { Inbox, Loader2, Zap } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { api } from "@/lib/api"

/**
 * 速记入口。
 *
 * 这是整套系统最关键的组件 —— 输入摩擦决定用户会不会一直用下去。
 * 所以只要求一段文本，类型、标题、报错原文全部后端推断。
 */
export function CaptureBox({ onCaptured }: { onCaptured: (id: string) => void }) {
  const [text, setText] = useState("")
  const [project, setProject] = useState("")
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hint, setHint] = useState<string | null>(null)

  async function submit() {
    if (!text.trim()) return
    setBusy(true)
    setError(null)
    try {
      const res = await api.capture(text, "web", project.trim() || undefined)
      setText("")
      setHint(`已存为「${res.record_type}」，自动抽取完成`)
      onCaptured(res.record_id)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="relative border-b border-rule bg-card/80 px-3 py-3.5 backdrop-blur">
      {/* 顶部小光晕 */}
      <div
        aria-hidden
        className="pointer-events-none absolute -left-10 -top-10 h-24 w-32 rounded-full bg-aurora-start/20 blur-2xl"
      />

      <div className="relative space-y-2">
        <div className="mb-1 flex items-center gap-1.5">
          <Zap className="h-3.5 w-3.5 text-ledger" />
          <span className="text-[13px] font-bold leading-5">速记</span>
          <span className="ml-auto data-num rounded bg-ledger/10 px-1.5 py-px text-[10px] font-bold text-ledger-ink">
            ⌘ ↵
          </span>
        </div>

        <div className="focus-glow rounded-md">
          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault()
                void submit()
              }
            }}
            placeholder={"粘一段报错、贴几句话、写一条注意事项"}
            className="min-h-[120px] resize-y border-ledger/30 text-xs leading-relaxed focus-visible:ring-0 focus-visible:border-ledger"
          />
        </div>

        <Input
          value={project}
          onChange={(e) => setProject(e.target.value)}
          placeholder="项目（可留空，事后补）"
          className="h-7 text-[11px]"
        />

        <Button
          onClick={() => void submit()}
          disabled={busy || !text.trim()}
          className="relative w-full overflow-hidden bg-ledger text-xs shadow-md shadow-ledger/20 hover:bg-ledger-ink"
          size="sm"
        >
          {busy && <Loader2 className="h-3 w-3 animate-spin" />}
          存进去
        </Button>
      </div>

      {hint && (
        <p className="relative mt-2 flex items-center gap-1 text-[11px] leading-4 text-pine-ink">
          <Inbox className="h-3 w-3" />
          {hint}
        </p>
      )}
      {error && (
        <p className="relative mt-2 text-[11px] leading-4 text-seal-ink">{error}</p>
      )}
    </div>
  )
}