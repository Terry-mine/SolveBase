import { useState } from "react"
import { Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { api } from "@/lib/api"
import type { Vocabulary } from "@/types"

/** 手动新建。日常建议直接用速记框，这里只作补充入口。 */
export function NewRecordDialog({
  vocab,
  onCreated,
}: {
  vocab: Vocabulary | null
  onCreated: (id: string) => void
}) {
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState("")
  const [recordType, setRecordType] = useState("incident")
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit() {
    if (!title.trim()) return
    setBusy(true)
    setError(null)
    try {
      const created = await api.create({ title: title.trim(), record_type: recordType })
      setOpen(false)
      setTitle("")
      onCreated(created.id)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          新建
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>新建记录</DialogTitle>
          <DialogDescription>只填标题即可，其余稍后在详情里补。</DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="一句话问题陈述"
          />
          <Select value={recordType} onValueChange={setRecordType}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {vocab?.types.map((t) => (
                <SelectItem key={t.key} value={t.key}>
                  {t.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {error && <p className="text-xs text-destructive">{error}</p>}

          <Button onClick={() => void submit()} disabled={busy || !title.trim()} className="w-full">
            {busy && <Loader2 className="h-3 w-3 animate-spin" />}
            创建
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
