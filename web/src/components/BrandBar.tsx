import { useEffect, useState } from "react"
import { Database } from "lucide-react"

import { CountUp } from "@/components/CountUp"

interface Props {
  total: number
}

/**
 * 顶部品牌栏。整条横贯渐变（玫瑰→薰衣草→天蓝），是页面的"门面"。
 * 配色取自壁纸的粉/蓝并压深，与下方壁纸同一族，避免上下两段色调打架。
 * 深色底上所有文字走白色体系：主文字纯白，次要文字 white/85（实测最低 4.51:1）。
 * 点缀色只能用亮青/亮琥珀这类高亮色，深色系在深底上会消失。
 */
export function BrandBar({ total }: Props) {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  const hh = String(now.getHours()).padStart(2, "0")
  const mm = String(now.getMinutes()).padStart(2, "0")
  const ss = String(now.getSeconds()).padStart(2, "0")

  const date = `${now.getFullYear()}.${String(now.getMonth() + 1).padStart(2, "0")}.${String(now.getDate()).padStart(2, "0")}`

  return (
    <header className="header-gradient relative z-10 flex h-14 shrink-0 items-center gap-3 overflow-hidden px-5">
      {/* 右上角柔和光斑，让渐变有纵深 */}
      <div
        aria-hidden
        className="pointer-events-none absolute -right-24 -top-24 h-56 w-80 rounded-full bg-[hsl(344_92%_74%)] opacity-30 blur-3xl"
      />
      {/* 左下角第二处光斑，避免右重左轻 */}
      <div
        aria-hidden
        className="pointer-events-none absolute -bottom-32 -left-16 h-48 w-64 rounded-full bg-[hsl(var(--on-dark-warn))] opacity-15 blur-3xl"
      />

      {/* Logo + 名称 */}
      <div className="relative flex items-center gap-2.5">
        <div className="relative flex h-8 w-8 items-center justify-center rounded-md bg-white/15 text-white ring-1 ring-white/25">
          <Database className="h-4 w-4" />
          {/* 角标：状态点呼吸 */}
          <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-[hsl(var(--on-dark-accent))] ring-2 ring-[hsl(var(--hdr-1))] animate-[glow-pulse_2.4s_ease-in-out_infinite]" />
        </div>
        <div className="flex flex-col leading-none">
          <span className="text-[17px] font-bold tracking-tight text-white">SolveBase</span>
          <span className="mt-0.5 text-[12px] text-white/85">故障排查档案库</span>
        </div>
      </div>

      {/* 分隔 */}
      <div className="mx-2 h-6 w-px bg-white/25" />

      {/* 状态指示 */}
      <div className="hidden items-center gap-3 text-[13px] text-white/85 md:flex">
        <span className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-[hsl(var(--on-dark-accent))] animate-[glow-pulse_2.4s_ease-in-out_infinite]" />
          本地运行中
        </span>
        <span className="data-num">
          共 <CountUp value={total} className="font-bold text-white" /> 条档案
        </span>
      </div>

      <div className="ml-auto flex items-center gap-3">
        {/* 日期 */}
        <span className="data-num hidden text-[13px] text-white/85 sm:inline">{date}</span>
        {/* 时钟：时分秒等宽 */}
        <div className="data-num flex items-baseline rounded-md border border-white/25 bg-white/12 px-2.5 py-1 tabular-nums">
          <span className="text-base font-bold leading-none text-white">{hh}</span>
          <span className="mx-0.5 text-base leading-none text-white/50">:</span>
          <span className="text-base font-bold leading-none text-white">{mm}</span>
          <span className="mx-0.5 text-base leading-none text-white/50">:</span>
          <span className="text-[15px] font-bold leading-none text-[hsl(var(--on-dark-warn))]">
            {ss}
          </span>
        </div>
      </div>

      {/* 周期性扫光：强化动态感 */}
      <div className="bar-sweep-ray" aria-hidden="true" />

      {/* 底部流动高光线 */}
      <div className="header-underline absolute inset-x-0 bottom-0 h-[2px]" />
    </header>
  )
}
