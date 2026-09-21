import { Link } from "@tanstack/react-router"

import { cn } from "@/lib/utils"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

/**
 * ScamGym 文字商標。
 *
 * 原本這裡直接引用 template 附帶的 fastapi-logo.svg，登入頁會掛著 FastAPI 的標誌。
 * 尚未有正式視覺識別前，先以文字商標取代，避免對外顯示錯誤品牌。
 * `variant` 的三種值沿用既有呼叫端語意：icon 只顯示縮寫，responsive 在側欄收合時退回縮寫。
 */
export function Logo({
  variant = "full",
  className,
  asLink = true,
}: LogoProps) {
  const wordmark = (
    <span className="whitespace-nowrap">
      <span className="font-bold tracking-tight">ScamGym</span>
      <span className="ml-2 text-muted-foreground">識詐練習場</span>
    </span>
  )
  const shortmark = <span className="font-bold tracking-tight">SG</span>

  const content =
    variant === "responsive" ? (
      <span
        className={cn("flex items-center text-base", className)}
        role="img"
        aria-label="ScamGym 識詐練習場"
      >
        <span className="group-data-[collapsible=icon]:hidden">{wordmark}</span>
        <span className="hidden group-data-[collapsible=icon]:block">
          {shortmark}
        </span>
      </span>
    ) : (
      <span
        className={cn(
          "flex items-center",
          variant === "full" ? "text-xl" : "text-base",
          className,
        )}
        role="img"
        aria-label="ScamGym 識詐練習場"
      >
        {variant === "full" ? wordmark : shortmark}
      </span>
    )

  if (!asLink) {
    return content
  }

  return <Link to="/pretest">{content}</Link>
}
