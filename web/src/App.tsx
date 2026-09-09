import { useCallback, useEffect, useState } from "react"
import { AlertCircle, Loader2, Search, Sparkles, X } from "lucide-react"

import { BrandBar } from "@/components/BrandBar"
import { CaptureBox } from "@/components/CaptureBox"
import { FacetSidebar } from "@/components/FacetSidebar"
import { NewRecordDialog } from "@/components/NewRecordDialog"
import { RecordDetail } from "@/components/RecordDetail"
import { RecordList } from "@/components/RecordList"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"
import { useWallpaperParallax } from "@/hooks/usePointer"
import { useDebounced, useVocabulary } from "@/hooks/useVocabulary"
import type { ListParams, RecordItem } from "@/types"

export default function App() {
  const { vocab } = useVocabulary()

  const [query, setQuery] = useState("")
  const [filters, setFilters] = useState<ListParams>({})
  const [items, setItems] = useState<RecordItem[]>([])
  const [total, setTotal] = useState(0)
  const [counts, setCounts] = useState<{
    types: Record<string, number>
    statuses: Record<string, number>
  }>({ types: {}, statuses: {} })

  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [selected, setSelected] = useState<RecordItem | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const debouncedQuery = useDebounced(query, 250)
  const wallpaperRef = useWallpaperParallax()

  const loadList = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const q = debouncedQuery.trim()
      const page = q
        ? await api.search(q)
        : await api.list({ ...filters, limit: 200, order: "updated" })
      setItems(page.items)
      setTotal(page.total)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }, [debouncedQuery, filters])

  const loadStats = useCallback(async () => {
    try {
      const s = await api.stats()
      setCounts({
        types: Object.fromEntries(s.by_type.map((b) => [b.key ?? "_none", b.count])),
        statuses: Object.fromEntries(s.by_status.map((b) => [b.key ?? "_none", b.count])),
      })
    } catch {
      /* 统计失败不影响主流程 */
    }
  }, [])

  const loadDetail = useCallback(async (id: string) => {
    try {
      setSelected(await api.get(id))
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }, [])

  useEffect(() => {
    void loadList()
  }, [loadList])

  useEffect(() => {
    void loadStats()
  }, [loadStats])

  useEffect(() => {
    if (!selectedId) {
      setSelected(null)
      return
    }
    void loadDetail(selectedId)
  }, [selectedId, loadDetail])

  const hasFilter = Boolean(
    filters.record_type || filters.category || filters.project || filters.status,
  )

  return (
    <div className="relative z-10 flex h-screen w-full flex-col overflow-hidden">
      {/* 全站壁纸背景（固定铺满 + 指针视差，玻璃面板压在它前面） */}
      <div className="app-wallpaper" ref={wallpaperRef} aria-hidden="true" />
      <BrandBar total={total} />

      <div className="relative z-10 flex flex-1 overflow-hidden">
      <FacetSidebar vocab={vocab} filters={filters} onChange={setFilters} counts={counts}>
        <CaptureBox onCaptured={(id) => void loadList().then(() => setSelectedId(id))} />
      </FacetSidebar>

      {/* 列表区 */}
      <section className="glass-strong flex w-[400px] shrink-0 flex-col border-r border-rule">
        <div className="space-y-2 border-b border-rule p-3">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="搜索标题、正文、报错原文"
              className="pl-8"
            />
          </div>

          <div className="flex items-center gap-2 text-[13px] leading-5 text-muted-foreground">
            {loading && <Loader2 className="h-3 w-3 animate-spin" />}
            <span className={loading ? "" : "data-num"}>{loading ? "检索中" : `${total} 条`}</span>
            {hasFilter && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-[13px]"
                onClick={() => setFilters({})}
              >
                <X className="h-3 w-3" />
                清除筛选
              </Button>
            )}
            <div className="ml-auto flex items-center gap-1">
              {debouncedQuery.trim() && <Badge variant="info">关键词模式</Badge>}
              <NewRecordDialog
                vocab={vocab}
                onCreated={(id) => void loadList().then(() => setSelectedId(id))}
              />
            </div>
          </div>

          {error && (
            <p className="flex items-center gap-1 text-[13px] leading-5 text-seal-ink">
              <AlertCircle className="h-3 w-3" />
              {error}
            </p>
          )}
        </div>

        <div className="flex-1 overflow-y-auto">
          <RecordList
            items={items}
            selectedId={selectedId}
            vocab={vocab}
            onSelect={setSelectedId}
          />
        </div>
      </section>

      {/* 详情区 */}
      <section className="glass min-w-0 flex-1 overflow-hidden">
        {selected ? (
          <RecordDetail
            record={selected}
            vocab={vocab}
            onSaved={() => {
              void loadList()
              void loadStats()
              void loadDetail(selected.id)
            }}
            onDeleted={() => {
              setSelectedId(null)
              void loadList()
              void loadStats()
            }}
          />
        ) : (
          <DetailEmpty />
        )}
      </section>
      </div>
    </div>
  )
}

function DetailEmpty() {
  return (
    <div className="relative flex h-full items-center justify-center overflow-hidden p-8">
      {/* 极光装饰背景 */}
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-1/2 h-[420px] w-[420px] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-25 blur-3xl aurora-bg"
      />
      {/* 网格装饰 */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 grid-bg opacity-30"
      />

      <div className="relative max-w-md space-y-5 text-center">
        {/* 标题区 */}
        <div className="relative mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-white/45 shadow-lg shadow-ledger/15 ring-1 ring-white/65 backdrop-blur-md">
          {/* 边框流光：空状态是页面焦点，用一圈跑动的光把视线引过去 */}
          <span className="beam-border rounded-2xl" aria-hidden="true" />
          <Sparkles className="h-7 w-7 text-ledger" />
          <span className="absolute -right-1 -top-1 h-3 w-3 animate-[glow-pulse_2.4s_ease-in-out_infinite] rounded-full bg-aurora-mid" />
        </div>

        <div className="space-y-2">
          <h2 className="text-xl font-bold tracking-tight">从左边选一条记录</h2>
          <p className="text-sm leading-relaxed text-muted-foreground">
            翻一下过去踩过的坑——比重新踩一遍划算得多。
          </p>
        </div>

        {/* 三个引导提示 */}
        <div className="grid grid-cols-1 gap-2 text-left text-[13px] leading-6 text-muted-foreground">
          <div className="flex items-start gap-2 rounded-md border border-white/50 bg-white/28 px-3 py-2">
            <span className="mt-0.5 text-ledger">▸</span>
            <span>点列表项，或用顶栏搜索框（Ctrl + K）</span>
          </div>
          <div className="flex items-start gap-2 rounded-md border border-white/50 bg-white/28 px-3 py-2">
            <span className="mt-0.5 text-ledger">▸</span>
            <span>侧栏可按类型 / 状态 / 项目过滤</span>
          </div>
          <div className="flex items-start gap-2 rounded-md border border-white/50 bg-white/28 px-3 py-2">
            <span className="mt-0.5 text-ledger">▸</span>
            <span>左下角速记框粘一段报错，自动建档</span>
          </div>
        </div>
      </div>
    </div>
  )
}
