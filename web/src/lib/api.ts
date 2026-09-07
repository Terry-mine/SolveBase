import type {
  ImageAsset,
  ListParams,
  Page,
  RecordItem,
  StatsBucket,
  Vocabulary,
} from "@/types"

const BASE = "/api/v1"

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body?.detail ?? JSON.stringify(body)
    } catch {
      /* 保持 statusText */
    }
    throw new Error(`${res.status} ${detail}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

function toQuery(params: Record<string, unknown>): string {
  const usp = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") usp.set(k, String(v))
  }
  const s = usp.toString()
  return s ? `?${s}` : ""
}

export const api = {
  health: () => request<Record<string, unknown>>("/health"),

  vocab: () => request<Vocabulary>("/vocab"),

  list: (params: ListParams) =>
    request<Page<RecordItem>>(`/records${toQuery(params as Record<string, unknown>)}`),

  search: (q: string, limit = 30) =>
    request<Page<RecordItem>>(`/records/search${toQuery({ q, limit })}`),

  stats: () =>
    request<{
      by_type: StatsBucket[]
      by_category: StatsBucket[]
      by_project: StatsBucket[]
      by_status: StatsBucket[]
    }>("/records/stats"),

  get: (id: string) => request<RecordItem>(`/records/${id}`),

  create: (data: Partial<RecordItem>) =>
    request<RecordItem>("/records", { method: "POST", body: JSON.stringify(data) }),

  patch: (id: string, data: Partial<RecordItem>) =>
    request<RecordItem>(`/records/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  remove: (id: string) => request<{ deleted: boolean }>(`/records/${id}`, { method: "DELETE" }),

  // 速记：title 硬性必填，图片作为独立资产随记录提交
  capture: (
    text: string,
    title: string,
    images: ImageAsset[] = [],
    source = "web",
    project?: string,
  ) =>
    request<{ record_id: string; record_type: string; title: string; needs_review: boolean }>(
      "/capture",
      { method: "POST", body: JSON.stringify({ text, title, images, source, project }) },
    ),

  /** 上传一张图片（粘贴截图用）。走 multipart，不能复用 request ——
   *  那个函数固定发 application/json，会把 FormData 的 boundary 冲掉。 */
  uploadImage: async (file: File): Promise<ImageAsset> => {
    const form = new FormData()
    form.append("file", file)
    const res = await fetch(BASE + "/images", { method: "POST", body: form })
    if (!res.ok) {
      let detail = res.statusText
      try {
        const body = await res.json()
        detail = body?.detail ?? JSON.stringify(body)
      } catch {
        /* 保持 statusText */
      }
      throw new Error(`${res.status} ${detail}`)
    }
    return res.json() as Promise<ImageAsset>
  },

  syncStatus: () => request<Record<string, unknown>>("/sync/status"),
}
