import { useEffect, useRef } from "react"

/** 全局共用一个 rAF 槽位，鼠标移动再快也只按帧写入 CSS 变量 */
let frame = 0

/**
 * 把指针在元素内的位置写成 CSS 变量 --mx / --my（px）。
 *
 * 刻意不走 React state：pointermove 每秒能触发上百次，
 * 每帧 setState 会把整棵列表重渲染一遍。写 CSS 变量则由合成器直接处理。
 *
 * 注意 currentTarget 必须在同步阶段取出来 —— 事件派发结束后它会被置空。
 */
export function glowOnMove(e: React.PointerEvent<HTMLElement>) {
  const el = e.currentTarget
  const { clientX, clientY } = e
  if (frame) return
  frame = requestAnimationFrame(() => {
    frame = 0
    const r = el.getBoundingClientRect()
    el.style.setProperty("--mx", `${clientX - r.left}px`)
    el.style.setProperty("--my", `${clientY - r.top}px`)
  })
}

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
