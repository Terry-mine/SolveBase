import { useState } from "react"
import { Inbox, Loader2 } from "lucide-react"

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
      setHint(`已存为「${res.record_type}」，自动抽取完成，可点击补全细节`)
      onCaptured(res.record_id)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-2 p-4">
      <div className="flex items-center gap-2 text-sm font-medium">
        <Inbox className="h-4 w-4" />
        速记
      </div>

      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
            e.preventDefault()
            void submit()
          }
        }}
        placeholder={"粘一段报错、贴几句话、写一条注意事项\nCmd/Ctrl + Enter 提交"}
        className="min-h-[120px] resize-y text-xs"
      />

      <Input
        value={project}
        onChange={(e) => setProject(e.target.value)}
        placeholder="项目（可留空，事后补）"
        className="h-8 text-xs"
      />

      <Button onClick={() => void submit()} disabled={busy || !text.trim()} className="w-full" size="sm">
        {busy && <Loader2 className="h-3 w-3 animate-spin" />}
        存进去
      </Button>

      {hint && <p className="text-xs text-emerald-700">{hint}</p>}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  )
}
