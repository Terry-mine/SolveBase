import { useEffect, useState } from "react"
import { Loader2, Save, Trash2 } from "lucide-react"

import { AttemptsEditor } from "@/components/AttemptsEditor"
import { CopyButton } from "@/components/CopyButton"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { api } from "@/lib/api"
import {
  categoryOptions,
  statusLabel,
  statusOptions,
  statusTone,
  typeLabel,
} from "@/lib/labels"
import { cn, formatTime } from "@/lib/utils"
import type { Attempt, ImageAsset, RecordItem, Vocabulary } from "@/types"

const str = (p: Record<string, unknown> | null | undefined, k: string): string =>
  !!p && typeof p[k] === "string" ? (p[k] as string) : ""

const arr = (p: Record<string, unknown> | null | undefined, k: string): string[] =>
  !!p && Array.isArray(p[k]) ? (p[k] as unknown[]).map(String) : []

/** 分区标题前的渐变短条配色（不能用动态类名，JIT 扫不到，走映射表） */
const TONE_BAR = {
  ledger: "bg-ledger",
  seal: "bg-seal",
  pine: "bg-pine",
  ochre: "bg-ochre",
} as const

type Tone = keyof typeof TONE_BAR

function Field({
  label,
  hint,
  children,
}: {
  label: string
  hint?: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-baseline gap-1.5">
        <span className="text-[11px] font-bold leading-4 text-muted-foreground">{label}</span>
        {hint && <span className="text-[10px] text-muted-foreground/70">{hint}</span>}
      </div>
      {children}
    </div>
  )
}

/** 档案分区：卡片承载，标题前一根渐变短条做分区标识 */
function Section({
  title,
  hint,
  tone = "ledger",
  children,
}: {
  title: string
  hint?: string
  tone?: Tone
  children: React.ReactNode
}) {
  return (
    <section className="detail-card space-y-2">
      <div className="flex items-center gap-2">
        <span className={cn("tone-bar", TONE_BAR[tone])} />
        <h3 className="text-[11px] font-bold leading-4 tracking-normal">{title}</h3>
        {hint && <span className="text-[10px] text-muted-foreground">{hint}</span>}
      </div>
      {children}
    </section>
  )
}

interface Props {
  record: RecordItem
  vocab: Vocabulary | null
  onSaved: () => void
  onDeleted: () => void
}

export function RecordDetail({ record, vocab, onSaved, onDeleted }: Props) {
  const [title, setTitle] = useState(record.title)
  const [status, setStatus] = useState(record.status)
  const [category, setCategory] = useState(record.category ?? "")
  const [project, setProject] = useState(record.project ?? "")
  const [systems, setSystems] = useState(record.systems.join(", "))
  const [tags, setTags] = useState(record.tags.join(", "))
  const [payload, setPayload] = useState<Record<string, unknown>>(record.payload ?? {})
  const [attempts, setAttempts] = useState<Attempt[]>(record.attempts ?? [])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [savedAt, setSavedAt] = useState<number | null>(null)

  useEffect(() => {
    setTitle(record.title)
    setStatus(record.status)
    setCategory(record.category ?? "")
    setProject(record.project ?? "")
    setSystems(record.systems.join(", "))
    setTags(record.tags.join(", "))
    setPayload(record.payload ?? {})
    setAttempts(record.attempts ?? [])
    setSavedAt(null)
  }, [record.id, record])

  const splitList = (s: string) =>
    s
      .split(/[,，]/)
      .map((x) => x.trim())
      .filter(Boolean)

  const splitLines = (s: string) =>
    s
      .split("\n")
      .map((x) => x.trim())
      .filter(Boolean)

  async function save() {
    setBusy(true)
    setError(null)
    try {
      const nextPayload: Record<string, unknown> = { ...payload }
      if (record.record_type === "runbook") {
        nextPayload.preconditions = splitLines(str(payload, "preconditions_text"))
        nextPayload.steps = splitLines(str(payload, "steps_text"))
      }
      await api.patch(record.id, {
        title,
        status,
        category: category || null,
        project: project || null,
        systems: splitList(systems),
        tags: splitList(tags),
        payload: nextPayload,
        attempts,
      })
      setSavedAt(Date.now())
      onSaved()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  async function remove() {
    if (!confirm(`确定删除「${record.title}」？删除后仍可在数据库里找回（软删）。`)) return
    setBusy(true)
    try {
      await api.remove(record.id)
      onDeleted()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
      setBusy(false)
    }
  }

  const setP = (k: string, v: unknown) => setPayload((prev) => ({ ...prev, [k]: v }))

  // 截图是独立资产：字节落盘在服务端，payload 里只有元信息。
  // 不混进 search_text，也不参与标题 —— 三者各自独立。
  const images = (Array.isArray(payload.images) ? payload.images : []) as ImageAsset[]

  return (
    <div className="flex h-full flex-col">
      {/* 头部：档案封皮（淡极光渐变 + 底部流动高光线） */}
      <div className="detail-hero relative space-y-2.5 border-b border-rule px-5 py-3.5">
        <div className="header-underline absolute inset-x-0 bottom-0 h-[2px] opacity-60" />

        <div className="flex items-start gap-3">
          <div className="min-w-0 flex-1 space-y-2">
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="h-9 border-transparent bg-transparent px-0 text-base font-bold shadow-none hover:border-input focus-visible:border-ledger focus-visible:ring-1 focus-visible:ring-ledger/30"
              placeholder="一句话问题陈述"
            />
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] leading-4">
              <span className="text-muted-foreground">
                {typeLabel(vocab, record.record_type)}
              </span>
              <Badge variant={statusTone(record.status)}>
                {statusLabel(vocab, record.record_type, record.status)}
              </Badge>
              {record.missing.length > 0 && (
                <Badge variant="destructive">待补全：{record.missing.join(" / ")}</Badge>
              )}
              {record.dirty === 1 && <Badge variant="outline">待同步</Badge>}
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-1">
            <Button size="sm" onClick={() => void save()} disabled={busy} className="text-xs">
              {busy ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />}
              保存
            </Button>
            <Button variant="ghost" size="icon" onClick={() => void remove()} disabled={busy}>
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        {savedAt && <p className="text-[11px] leading-4 text-pine-ink">已保存</p>}
        {error && <p className="text-[11px] leading-4 text-seal-ink">{error}</p>}
      </div>

      {/* 三栏内容 */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        <div className="grid grid-cols-1 gap-x-6 gap-y-4 xl:grid-cols-3">
          {/* 左：分类与上下文 */}
          <div className="space-y-4">
            <Section title="分类" tone="ledger">
              <div className="grid grid-cols-2 gap-2">
                <Field label="状态">
                  <Select value={status} onValueChange={setStatus}>
                    <SelectTrigger className="h-7 text-[11px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {statusOptions(vocab, record.record_type).map((s) => (
                        <SelectItem key={`${s.code}-${s.label}`} value={s.code} className="text-xs">
                          {s.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </Field>

                <Field label="类别">
                  <Select
                    value={category || "__none__"}
                    onValueChange={(v) => setCategory(v === "__none__" ? "" : v)}
                  >
                    <SelectTrigger className="h-7 text-[11px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__" className="text-xs">
                        未分类
                      </SelectItem>
                      {categoryOptions(vocab, record.record_type).map((c) => (
                        <SelectItem key={c.code} value={c.code} className="text-xs">
                          {c.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </Field>
              </div>

              <Field label="项目">
                <Input
                  value={project}
                  onChange={(e) => setProject(e.target.value)}
                  className="h-7 text-[11px]"
                  placeholder="归属项目"
                />
              </Field>

              <Field label="涉及系统" hint="逗号分隔">
                <Input
                  value={systems}
                  onChange={(e) => setSystems(e.target.value)}
                  className="h-7 text-[11px]"
                  placeholder="Docker, PostgreSQL"
                />
              </Field>

              <Field label="标签" hint="逗号分隔">
                <Input
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  className="h-7 text-[11px]"
                />
              </Field>
            </Section>

            {record.record_type === "incident" && (
              <Section title="报错原文" tone="seal">
                {record.error_excerpt ? (
                  <>
                    {/* 全页唯一的深色块：报错本来就是从终端里蹦出来的 */}
                    <div className="code-block">{record.error_excerpt}</div>
                    <CopyButton text={record.error_excerpt} />
                  </>
                ) : (
                  <p className="text-[11px] leading-4 text-muted-foreground">未识别到报错原文</p>
                )}
              </Section>
            )}

            {images.length > 0 && (
              <Section title="截图" hint={`${images.length} 张`} tone="ledger">
                <div className="flex flex-wrap gap-2">
                  {images.map((img) => (
                    <a
                      key={img.id}
                      href={img.url}
                      target="_blank"
                      rel="noreferrer"
                      className="block h-20 w-20 overflow-hidden rounded border border-rule transition-colors hover:border-ledger"
                    >
                      <img src={img.url} alt="" className="h-full w-full object-cover" />
                    </a>
                  ))}
                </div>
              </Section>
            )}

            <Section title="原始记录" tone="ochre">
              <div className="raw-block">{record.search_text || "（空）"}</div>
            </Section>
          </div>

          {/* 中：类型专属主体 */}
          <div className="space-y-4">
            {record.record_type === "incident" && (
              <>
                <Section title="尝试时间线" tone="pine">
                  <AttemptsEditor attempts={attempts} onChange={setAttempts} />
                </Section>
                <Section title="根因" tone="seal">
                  <Textarea
                    value={str(payload, "root_cause")}
                    onChange={(e) => setP("root_cause", e.target.value)}
                    className="min-h-[80px] text-xs leading-relaxed"
                    placeholder="为什么会出这个问题"
                  />
                </Section>
                <Section title="解法" tone="pine">
                  <Textarea
                    value={str(payload, "solution")}
                    onChange={(e) => setP("solution", e.target.value)}
                    className="min-h-[100px] text-xs leading-relaxed"
                    placeholder="可执行的步骤"
                  />
                </Section>
                <Section title="如何避免再次发生" tone="ledger">
                  <Textarea
                    value={str(payload, "prevention")}
                    onChange={(e) => setP("prevention", e.target.value)}
                    className="min-h-[60px] text-xs leading-relaxed"
                  />
                </Section>
              </>
            )}

            {record.record_type === "runbook" && (
              <>
                <Section title="前置条件" hint="一行一条" tone="ledger">
                  <Textarea
                    value={
                      str(payload, "preconditions_text") ||
                      arr(payload, "preconditions").join("\n")
                    }
                    onChange={(e) => setP("preconditions_text", e.target.value)}
                    className="min-h-[80px] text-xs leading-relaxed"
                  />
                </Section>
                <Section title="步骤" hint="一行一步" tone="pine">
                  <Textarea
                    value={str(payload, "steps_text") || arr(payload, "steps").join("\n")}
                    onChange={(e) => setP("steps_text", e.target.value)}
                    className="min-h-[160px] text-xs leading-relaxed"
                  />
                </Section>
                <Section title="校验点" tone="ochre">
                  <Textarea
                    value={str(payload, "verify")}
                    onChange={(e) => setP("verify", e.target.value)}
                    className="min-h-[60px] text-xs leading-relaxed"
                    placeholder="怎么确认这一步做对了"
                  />
                </Section>
                <Section title="回滚方案" tone="seal">
                  <Textarea
                    value={str(payload, "rollback")}
                    onChange={(e) => setP("rollback", e.target.value)}
                    className="min-h-[80px] text-xs leading-relaxed"
                  />
                </Section>
              </>
            )}

            {record.record_type === "note" && (
              <>
                <Section title="结论" tone="pine">
                  <Textarea
                    value={str(payload, "conclusion")}
                    onChange={(e) => setP("conclusion", e.target.value)}
                    className="min-h-[80px] text-xs leading-relaxed"
                    placeholder="这条注意事项到底是什么"
                  />
                </Section>
                <Section title="适用场景" tone="ledger">
                  <Textarea
                    value={str(payload, "scenario")}
                    onChange={(e) => setP("scenario", e.target.value)}
                    className="min-h-[60px] text-xs leading-relaxed"
                  />
                </Section>
                <Section title="为什么" hint="当初踩过什么坑" tone="ochre">
                  <Textarea
                    value={str(payload, "reason")}
                    onChange={(e) => setP("reason", e.target.value)}
                    className="min-h-[80px] text-xs leading-relaxed"
                  />
                </Section>
              </>
            )}
          </div>

          {/* 右：元信息 */}
          <div className="space-y-4">
            <Section title="记录信息" tone="ochre">
              <dl className="space-y-1.5 text-[11px] leading-4">
                {[
                  ["创建", formatTime(record.created_at)],
                  ["更新", formatTime(record.updated_at)],
                  ["查看次数", String(record.hit_count)],
                  ["版本号", `rev ${record.rev}`],
                  ["来源设备", record.device_id],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-3">
                    <dt className="shrink-0 text-muted-foreground">{k}</dt>
                    <dd className="data-num truncate text-right">{v}</dd>
                  </div>
                ))}
              </dl>
            </Section>
          </div>
        </div>
      </div>
    </div>
  )
}
