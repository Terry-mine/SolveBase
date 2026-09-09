import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

/**
 * 徽章。
 *
 * 档案方向：扁、紧、无阴影，靠底色浓淡区分语义，不靠圆角和投影。
 * 状态类信息优先用列表左侧色条承载，徽章只用于必须点名的场合。
 */
const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-sm border px-1.5 py-px text-[13px] leading-5 font-normal whitespace-nowrap",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        destructive: "border-transparent bg-seal/10 text-seal-ink",
        outline: "border-rule bg-transparent text-muted-foreground",
        success: "border-transparent bg-pine/10 text-pine-ink",
        warning: "border-transparent bg-ochre/12 text-ochre-ink",
        info: "border-transparent bg-ledger/10 text-ledger-ink",
      },
    },
    defaultVariants: { variant: "default" },
  },
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
