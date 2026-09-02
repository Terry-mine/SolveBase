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
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { api } from "@/lib/api"
import { categoryOptions, statusOptions, statusTone, typeLabel } from "@/lib/labels"
import { formatTime } from "@/lib/utils"
import type { Attempt, RecordItem, Vocabulary } from "@/types"

const str = (p: Record<string, unknown> | null | undefined, k: string): string =>
  !!p && typeof p[k] === "string" ? (p[k] as string) : ""

const arr = (p: Record<string, unknown> | null | undefined, k: string): string[] =>
  !!p && Array.isArray(p[k]) ? (p[k] as unknown[]).map(String) : []

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
      <div className="flex items-baseline gap-2">
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
        {hint && <span className="text-[11px] text-muted-foreground/70">{hint}</span>}
      </div>
      {children}
    </div>
  )
}

function Section({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <div className="flex items-baseline gap-2">
        <span className="text-xs font-medium">{title}</span>
        {hint && <span className="text-[10px] text-muted-foreground">{hint}</span>}
      </div>
      {children}
    </div>
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

  return (
    <div className="flex h-full flex-col">
      {/* 头部 */}
      <div className="space-y-3 border-b p-4">
        <div className="flex items-start gap-2">
          <div className="flex-1 space-y-2">
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="h-8 text-sm font-medium"
              placeholder="一句话问题陈述"
            />
            <div className="flex flex-wrap items-center gap-1.5">
              <Badge variant="outline" className="font-normal">
                {typeLabel(vocab, record.record_type)}
              </Badge>
              {record.missing.length > 0 && (
                <Badge variant="warning" className="font-normal">
                  待补全：{record.missing.join(" / ")}
                </Badge>
              )}
              {record.dirty === 1 && (
                <Badge variant="secondary" className="font-normal">
                  待同步
                </Badge>
              )}
            </div>
          </div>

          <div className="flex shrink-0 gap-1">
            <Button size="sm" onClick={() => void save()} disabled={busy}>
              {busy ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />}
              保存
            </Button>
            <Button variant="ghost" size="icon" onClick={() => void remove()} disabled={busy}>
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        </div>

        {savedAt && <p className="text-xs text-emerald-700">已保存</p>}
        {error && <p className="text-xs text-destructive">{error}</p>}
      </div>

      {/* 三栏内容 */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
          {/* 左：症状与上下文 */}
          <div className="space-y-4">
            <Section title="分类">
              <div className="grid grid-cols-2 gap-2">
                <Field label="状态">
                  <Select value={status} onValueChange={setStatus}>
                    <SelectTrigger className="h-8 text-xs">
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
                    <SelectTrigger className="h-8 text-xs">
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
                  className="h-8 text-xs"
                  placeholder="归属项目"
                />
              </Field>

              <Field label="涉及系统" hint="逗号分隔，可多个">
                <Input
                  value={systems}
                  onChange={(e) => setSystems(e.target.value)}
                  className="h-8 text-xs"
                  placeholder="Docker, PostgreSQL"
                />
              </Field>

              <Field label="标签" hint="逗号分隔">
                <Input
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  className="h-8 text-xs"
                />
              </Field>
            </Section>

            {record.record_type === "incident" && (
              <Section title="报错原文">
                {record.error_excerpt ? (
                  <>
                    <div className="code-block">{record.error_excerpt}</div>
                    <CopyButton text={record.error_excerpt} />
                  </>
                ) : (
                  <p className="text-xs text-muted-foreground">未识别到报错原文</p>
                )}
              </Section>
            )}

            <Section title="原始记录">
              <div className="code-block max-h-52 overflow-y-auto">
                {record.search_text || "（空）"}
              </div>
            </Section>
          </div>

          {/* 中：类型专属主体 */}
          <div className="space-y-4">
            {record.record_type === "incident" && (
              <>
                <Section title="尝试时间线">
                  <AttemptsEditor attempts={attempts} onChange={setAttempts} />
                </Section>
                <Separator />
                <Section title="根因">
                  <Textarea
                    value={str(payload, "root_cause")}
                    onChange={(e) => setP("root_cause", e.target.value)}
                    className="min-h-[80px] text-xs"
                    placeholder="为什么会出这个问题"
                  />
                </Section>
                <Section title="解法">
                  <Textarea
                    value={str(payload, "solution")}
                    onChange={(e) => setP("solution", e.target.value)}
                    className="min-h-[100px] text-xs"
                    placeholder="可执行的步骤"
                  />
                </Section>
                <Section title="如何避免再次发生">
                  <Textarea
                    value={str(payload, "prevention")}
                    onChange={(e) => setP("prevention", e.target.value)}
                    className="min-h-[60px] text-xs"
                  />
                </Section>
              </>
            )}

            {record.record_type === "runbook" && (
              <>
                <Section title="前置条件" hint="一行一条">
                  <Textarea
                    value={str(payload, "preconditions_text") || arr(payload, "preconditions").join("\n")}
                    onChange={(e) => setP("preconditions_text", e.target.value)}
                    className="min-h-[80px] text-xs"
                  />
                </Section>
                <Section title="步骤" hint="一行一步">
                  <Textarea
                    value={str(payload, "steps_text") || arr(payload, "steps").join("\n")}
                    onChange={(e) => setP("steps_text", e.target.value)}
                    className="min-h-[160px] text-xs"
                  />
                </Section>
                <Section title="校验点">
                  <Textarea
                    value={str(payload, "verify")}
                    onChange={(e) => setP("verify", e.target.value)}
                    className="min-h-[60px] text-xs"
                    placeholder="怎么确认这一步做对了"
                  />
                </Section>
                <Section title="回滚方案">
                  <Textarea
                    value={str(payload, "rollback")}
                    onChange={(e) => setP("rollback", e.target.value)}
                    className="min-h-[80px] text-xs"
                  />
                </Section>
              </>
            )}

            {record.record_type === "note" && (
              <>
                <Section title="结论">
                  <Textarea
                    value={str(payload, "conclusion")}
                    onChange={(e) => setP("conclusion", e.target.value)}
                    className="min-h-[80px] text-xs"
                    placeholder="这条注意事项到底是什么"
                  />
                </Section>
                <Section title="适用场景">
                  <Textarea
                    value={str(payload, "scenario")}
                    onChange={(e) => setP("scenario", e.target.value)}
                    className="min-h-[60px] text-xs"
                  />
                </Section>
                <Section title="为什么" hint="当初踩过什么坑">
                  <Textarea
                    value={str(payload, "reason")}
                    onChange={(e) => setP("reason", e.target.value)}
                    className="min-h-[80px] text-xs"
                  />
                </Section>
              </>
            )}
          </div>

          {/* 右：元信息 */}
          <div className="space-y-4">
            <Section title="记录信息">
              <dl className="space-y-1.5 text-xs">
                {[
                  ["创建", formatTime(record.created_at)],
                  ["更新", formatTime(record.updated_at)],
                  ["查看次数", String(record.hit_count)],
                  ["版本号", `rev ${record.rev}`],
                  ["来源设备", record.device_id],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-2">
                    <dt className="text-muted-foreground">{k}</dt>
                    <dd className="truncate">{v}</dd>
                  </div>
                ))}
              </dl>
              <Badge variant={statusTone(record.status)} className="font-normal">
                {status}
              </Badge>
            </Section>
          </div>
        </div>
      </div>
    </div>
  )
}
