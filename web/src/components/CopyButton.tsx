import { useState } from "react"
import { Check, Copy } from "lucide-react"

import { Button } from "@/components/ui/button"

/** 复制按钮。复制次数会回流成热度，影响检索排序。 */
export function CopyButton({ text, label = "复制" }: { text: string; label?: string }) {
  const [done, setDone] = useState(false)

  async function copy() {
    try {
      await navigator.clipboard.writeText(text)
      setDone(true)
      setTimeout(() => setDone(false), 1500)
    } catch {
      /* 剪贴板不可用时静默失败，不打断操作 */
    }
  }

  return (
    <Button variant="ghost" size="sm" onClick={copy} className="h-7 px-2 text-xs">
      {done ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
      {done ? "已复制" : label}
    </Button>
  )
}
