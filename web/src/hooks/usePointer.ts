import { useEffect, useRef } from "react"

/** 是否应当关闭动效（尊重系统「减弱动态效果」） */
export function prefersReducedMotion() {
  return (
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  )
}

/**
 * 壁纸视差：指针移动时壁纸反向轻移，玻璃面板压在上面不动，
 * 于是产生「玻璃浮在景色前面」的纵深。
 */
export function useWallpaperParallax() {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    if (prefersReducedMotion()) return

    let raf = 0
    const onMove = (e: PointerEvent) => {
      if (raf) return
      raf = requestAnimationFrame(() => {
        raf = 0
        const x = (e.clientX / window.innerWidth - 0.5) * 2 // -1 ~ 1
        const y = (e.clientY / window.innerHeight - 0.5) * 2
        el.style.transform = `translate3d(${x * -20}px, ${y * -15}px, 0)`
      })
    }

    window.addEventListener("pointermove", onMove, { passive: true })
    return () => {
      window.removeEventListener("pointermove", onMove)
      if (raf) cancelAnimationFrame(raf)
    }
  }, [])

  return ref
}
