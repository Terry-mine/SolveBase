import { useState } from "react"
import { ImageIcon, Inbox, Loader2, X, Zap } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { api } from "@/lib/api"
import type { ImageAsset } from "@/types"

/**
 * 速记入口。
 *
 * 这是整套系统最关键的组件 —— 输入摩擦决定用户会不会一直用下去。
 *
 * 两条硬规矩：
 * 1. title 必填。自动推断的标题常常抓不住重点，事后回头补比当场填更贵。
 * 2. 图片是独立资产。截图落盘存元信息，不混进原始记录文本，也不塞进标题。
 *    ocr 字段留给将来的「识别图中文字 → 填报错原文」，现在一直是 pending。
 */
export function CaptureBox({ onCaptured }: { onCaptured: (id: string) => void }) {
  const [title, setTitle] = useState("")
  const [text, setText] = useState("")
  const [images, setImages] = useState<ImageAsset[]>([])
  const [project, setProject] = useState("")
  const [busy, setBusy] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hint, setHint] = useState<string | null>(null)

  const titleMissing = title.trim().length === 0

  async function addFiles(files: File[]) {
    if (files.length === 0) return
    setUploading(true)
    setError(null)
    try {
      const assets = await Promise.all(files.map((f) => api.uploadImage(f)))
      setImages((prev) => [...prev, ...assets])
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setUploading(false)
    }
  }

  /** 粘贴图片。只拦截真的带图的粘贴，纯文本照常输入，不打断打字。 */
  function handlePaste(e: React.ClipboardEvent<HTMLTextAreaElement>) {
    const files: File[] = []
    for (const item of Array.from(e.clipboardData?.items ?? [])) {
      if (item.kind === "file" && item.type.startsWith("image/")) {
        const f = item.getAsFile()
        if (f) files.push(f)
      }
    }
    if (files.length === 0) return
    e.preventDefault()
    void addFiles(files)
  }

  async function submit() {
    if (titleMissing) return
    setBusy(true)
    setError(null)
    try {
      const res = await api.capture(
        text,
        title.trim(),
        images,
        "web",
        project.trim() || undefined,
      )
      setTitle("")
      setText("")
      setImages([])
      setHint(
        images.length > 0
          ? `已存为「${res.record_type}」，含 ${images.length} 张截图`
          : `已存为「${res.record_type}」，自动抽取完成`,
      )
      onCaptured(res.record_id)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="relative border-b border-rule bg-white/25 px-3 py-3.5">
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

        {/* 标题：硬性必填，和原始记录分开填 */}
        <div className="space-y-1">
          <div className="flex items-center gap-1">
            <span className="text-[11px] font-bold leading-4">
              标题<span className="text-seal-ink"> *</span>
            </span>
            {titleMissing && (
              <span className="text-[10px] text-muted-foreground">必填，一句话说清问题</span>
            )}
          </div>
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault()
                void submit()
              }
            }}
            placeholder="一句话问题陈述（必填）"
            className={
              titleMissing
                ? "h-8 border-seal/40 text-xs"
                : "h-8 border-pine/40 text-xs focus-visible:border-pine"
            }
          />
        </div>

        {/* 详情：截图可以直接 Ctrl+V 粘进来 */}
        <div className="focus-glow rounded-md">
          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onPaste={handlePaste}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault()
                void submit()
              }
            }}
            placeholder={"粘一段报错、贴几句话、写一条注意事项\n截图可直接 ⌘/Ctrl + V 粘进来"}
            className="min-h-[100px] resize-y border-ledger/30 text-xs leading-relaxed focus-visible:border-ledger focus-visible:ring-0"
          />
        </div>

        {/* 图片预览：上传中给个提示，hover 出删除 */}
        {images.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            {images.map((img) => (
              <div
                key={img.id}
                className="group relative h-14 w-14 overflow-hidden rounded border border-rule bg-secondary"
              >
                <img src={img.url} alt="" className="h-full w-full object-cover" />
                <button
                  type="button"
                  aria-label="移除这张图"
                  onClick={() => setImages((prev) => prev.filter((x) => x.id !== img.id))}
                  className="absolute right-0 top-0 flex h-4 w-4 items-center justify-center bg-ink/70 text-white opacity-0 transition-opacity group-hover:opacity-100"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
            {uploading && (
              <div className="flex h-14 w-14 items-center justify-center rounded border border-dashed border-rule">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
              </div>
            )}
          </div>
        )}
        {uploading && images.length === 0 && (
          <p className="flex items-center gap-1 text-[11px] leading-4 text-muted-foreground">
            <ImageIcon className="h-3 w-3" />
            图片上传中
          </p>
        )}

        <Input
          value={project}
          onChange={(e) => setProject(e.target.value)}
          placeholder="项目（可留空，事后补）"
          className="h-7 text-[11px]"
        />

        <Button
          onClick={() => void submit()}
          disabled={busy || titleMissing}
          className="group relative w-full overflow-hidden bg-ledger text-xs shadow-md shadow-ledger/20 hover:bg-ledger-ink disabled:opacity-50"
          size="sm"
        >
          {/* 悬停时一道高光掠过：可点的按钮才掠，禁用态不掠 */}
          {!busy && !titleMissing && (
            <span
              aria-hidden
              className="pointer-events-none absolute inset-y-0 left-0 w-1/2 -translate-x-[140%] skew-x-[-18deg] bg-white/30 group-hover:animate-[sheen_1.05s_ease-out]"
            />
          )}
          {busy && <Loader2 className="h-3 w-3 animate-spin" />}
          <span className="relative">{titleMissing ? "先填标题" : "存进去"}</span>
        </Button>
      </div>

      {hint && (
        <p className="relative mt-2 flex items-center gap-1 text-[11px] leading-4 text-pine-ink">
          <Inbox className="h-3 w-3" />
          {hint}
        </p>
      )}
      {error && <p className="relative mt-2 text-[11px] leading-4 text-seal-ink">{error}</p>}
    </div>
  )
}
