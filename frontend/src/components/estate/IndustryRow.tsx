import { Lock, UserRoundPlus } from "lucide-react"
import type { IndustryPublic } from "@/client"
import { cn } from "@/lib/utils"
import { parseBigIntSafe } from "@/utils/money"
import { projectIndustry } from "./estateClock"
import { formatCycle, formatYuan, perSecond } from "./format"

/**
 * 一列產業：圖、經理頭像、名稱與間數、收租進度條、每秒收入、「再買一間」。
 * 點名稱打開詳情（升級卡、翻倍進度），點頭像換經理。
 */
export function IndustryRow({
  industry,
  elapsed,
  cash,
  busy,
  onBuy,
  onCollect,
  onDetail,
  onManager,
}: {
  industry: IndustryPublic
  elapsed: number
  cash: bigint
  busy: boolean
  onBuy: () => void
  onCollect: () => void
  onDetail: () => void
  onManager: () => void
}) {
  const now = projectIndustry(industry, elapsed)
  const owned = industry.owned > 0
  const price = parseBigIntSafe(industry.next_price)
  const affordable = cash >= price
  return (
    <li
      data-testid={`industry-${industry.tier_id}`}
      className={cn(
        "rounded-2xl border border-border bg-card p-3",
        !owned && "bg-surface-2/60",
      )}
    >
      <div className="flex items-center gap-3">
        <div className="relative shrink-0">
          <img
            src={industry.image_url}
            alt=""
            className={cn(
              "size-16 rounded-xl bg-surface-2 object-cover",
              !owned && "opacity-50 grayscale",
            )}
          />
          {owned && (
            <button
              type="button"
              onClick={onManager}
              aria-label={
                industry.manager
                  ? `經理：${industry.manager.name}，點一下換經理`
                  : "派經理"
              }
              data-testid={`manager-${industry.tier_id}`}
              className="absolute -right-2 -bottom-2 flex size-8 items-center justify-center overflow-hidden rounded-full border-2 border-card bg-surface-3 shadow"
            >
              {industry.manager ? (
                <img
                  src={industry.manager.image_url}
                  alt=""
                  className="size-full object-contain"
                />
              ) : (
                <UserRoundPlus
                  aria-hidden
                  className="size-4 text-muted-foreground"
                />
              )}
            </button>
          )}
        </div>

        <div className="min-w-0 flex-1">
          <button
            type="button"
            onClick={onDetail}
            className="flex w-full items-baseline justify-between gap-2 text-left"
          >
            <span className="truncate font-bold">{industry.name}</span>
            <span className="shrink-0 text-sm tabular-nums text-muted-foreground">
              {owned ? `${industry.owned} 間` : "還沒有"}
            </span>
          </button>
          {owned ? (
            <>
              <div
                className="mt-2 h-3 overflow-hidden rounded-full bg-surface-2"
                role="progressbar"
                aria-label={`${industry.name}收租進度`}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={Math.round(now.progress * 100)}
              >
                <div
                  className={cn(
                    "h-full rounded-full",
                    now.ready ? "bg-warning" : "bg-legit",
                  )}
                  style={{ width: `${now.progress * 100}%` }}
                />
              </div>
              <p className="mt-1 flex justify-between text-xs tabular-nums text-muted-foreground">
                <span>每秒 {perSecond(industry.income_per_hour)} 元</span>
                <span>
                  {industry.manager ? "自動收租" : "要自己收"}・
                  {formatCycle(industry.cycle_seconds)}一次
                </span>
              </p>
            </>
          ) : (
            <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
              <Lock aria-hidden className="size-3" />
              {formatCycle(industry.cycle_seconds)}收一次租，對應「
              {industry.category_label}」
            </p>
          )}
        </div>
      </div>

      <div className="mt-3 flex gap-2">
        {owned && now.ready && (
          <button
            type="button"
            disabled={busy}
            onClick={onCollect}
            data-testid={`collect-${industry.tier_id}`}
            className="flex-1 rounded-xl bg-warning px-3 py-2 font-bold text-warning-foreground"
          >
            收租 {formatYuan(industry.revenue_per_cycle)} 元
          </button>
        )}
        <button
          type="button"
          disabled={busy || !affordable}
          onClick={onBuy}
          data-testid={`buy-${industry.tier_id}`}
          className={cn(
            "flex flex-1 flex-col items-center rounded-xl px-3 py-1.5 font-bold",
            affordable
              ? "bg-primary text-primary-foreground"
              : "bg-surface-2 text-muted-foreground",
          )}
        >
          <span className="text-sm">{owned ? "再買一間" : "買第一間"}</span>
          <span className="text-xs tabular-nums opacity-90">
            {formatYuan(price)} 元
          </span>
        </button>
      </div>
    </li>
  )
}
