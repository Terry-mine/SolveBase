import { useCallback, useEffect, useState } from "react"
import { AlertCircle, Loader2, Search, X } from "lucide-react"

import { CaptureBox } from "@/components/CaptureBox"
import { FacetSidebar } from "@/components/FacetSidebar"
import { NewRecordDialog } from "@/components/NewRecordDialog"
import { RecordDetail } from "@/components/RecordDetail"
import { RecordList } from "@/components/RecordList"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"
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
    <div className="flex h-screen w-full overflow-hidden bg-background">
      <FacetSidebar vocab={vocab} filters={filters} onChange={setFilters} counts={counts}>
        <CaptureBox onCaptured={(id) => void loadList().then(() => setSelectedId(id))} />
      </FacetSidebar>

      {/* 列表区 */}
      <section className="flex w-[400px] shrink-0 flex-col border-r">
        <div className="space-y-2 border-b p-3">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="搜索标题、正文、报错原文"
              className="pl-8"
            />
          </div>

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {loading && <Loader2 className="h-3 w-3 animate-spin" />}
            <span>{loading ? "检索中" : `${total} 条`}</span>
            {hasFilter && (
              <Button
                variant="ghost"
                size="sm"
                className="h-5 px-1.5 text-xs"
                onClick={() => setFilters({})}
              >
                <X className="h-3 w-3" />
                清除筛选
              </Button>
            )}
            <div className="ml-auto flex items-center gap-1">
              {debouncedQuery.trim() && <Badge variant="secondary">关键词模式</Badge>}
              <NewRecordDialog
                vocab={vocab}
                onCreated={(id) => void loadList().then(() => setSelectedId(id))}
              />
            </div>
          </div>

          {error && (
            <p className="flex items-center gap-1 text-xs text-destructive">
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
      <section className="min-w-0 flex-1 overflow-hidden">
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
          <div className="flex h-full items-center justify-center p-8 text-center text-sm text-muted-foreground">
            从左边选一条记录查看详情
          </div>
        )}
      </section>
    </div>
  )
}
