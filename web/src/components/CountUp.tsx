import { useEffect, useRef, useState } from "react"

import { prefersReducedMotion } from "@/hooks/usePointer"

interface Props {
  value: number
  duration?: number
  className?: string
}

const easeOut = (t: number) => 1 - Math.pow(1 - t, 3)

/**
 * 数字滚动。只在数值变化时跑一次 rAF 补间，之后停在终值不动。
 * 用于顶栏的档案总数——列表刷新时数字跳变比静止的更有反馈感。
 */
export function CountUp({ value, duration = 700, className }: Props) {
  const [display, setDisplay] = useState(value)
  const fromRef = useRef(value)
  const rafRef = useRef(0)

  useEffect(() => {
    const from = fromRef.current
    if (from === value) return

    if (prefersReducedMotion()) {
      fromRef.current = value
      setDisplay(value)
      return
    }

    const start = performance.now()
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration)
      setDisplay(Math.round(from + (value - from) * easeOut(t)))
      if (t < 1) {
        rafRef.current = requestAnimationFrame(tick)
      } else {
        fromRef.current = value
      }
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [value, duration])

  return (
    <span className={className} style={{ animation: "tick-up 0.3s ease-out" }}>
      {display}
    </span>
  )
}
