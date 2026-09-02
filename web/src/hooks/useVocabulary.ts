import { useEffect, useState } from "react"

import { api } from "@/lib/api"
import type { Vocabulary } from "@/types"

/** 词表从 /api/v1/vocab 取，不硬编码。
 *  改完 config/vocab.yaml 执行一次 seed，刷新页面即生效。 */
export function useVocabulary() {
  const [vocab, setVocab] = useState<Vocabulary | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .vocab()
      .then(setVocab)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
  }, [])

  return { vocab, error }
}

export function useDebounced<T>(value: T, delay = 250): T {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debounced
}
