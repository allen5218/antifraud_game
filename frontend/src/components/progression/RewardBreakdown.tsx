import { Coins, Hammer, ReceiptText, Sparkles, Zap } from "lucide-react"
import { useState } from "react"
import type { RewardReceiptSchema } from "@/client"
import { formatMoney } from "@/utils/money"
import { formatFactor } from "@/utils/progressionDisplay"

interface RewardBreakdownProps {
  receipt?: RewardReceiptSchema | null
  className?: string
}

export function RewardBreakdown({
  receipt,
  className = "",
}: RewardBreakdownProps) {
  const [showDetails, setShowDetails] = useState(false)

  if (!receipt) return null

  const cashFinal = receipt.final?.cash_total ?? "0"
  const cashBonus = receipt.final?.cash_bonus ?? "0"
  const growthXp = receipt.final?.growth_xp ?? "0"
  const energy = receipt.final?.forge_energy ?? "0"
  const fixedCash = receipt.final?.fixed_cash ?? "0"

  const cashFactor = formatFactor(receipt.factors?.cash)
  const growthXpFactor = formatFactor(receipt.factors?.growth_xp)
  const energyFactor = formatFactor(receipt.factors?.energy)

  const levelUp = receipt.core_level_after > receipt.core_level_before

  return (
    <div
      className={`w-full rounded-xl border border-border bg-card p-3.5 text-left text-card-foreground shadow-xs ${className}`}
    >
      {levelUp && (
        <div className="mb-2.5 flex items-center gap-1.5 rounded-lg border border-primary/30 bg-primary/10 px-2.5 py-1.5 text-xs font-bold text-primary">
          <Sparkles className="size-4 shrink-0" aria-hidden="true" />
          <span>
            核心等級提升至 Lv.{receipt.core_level_after}！常規能力全面放大
          </span>
        </div>
      )}

      <div className="mb-2 flex items-center justify-between">
        <span className="flex items-center gap-1.5 text-xs font-bold text-muted-foreground">
          <Sparkles className="size-3.5" aria-hidden="true" />
          倍率加成結算
        </span>
        <button
          type="button"
          onClick={() => setShowDetails((prev) => !prev)}
          className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground"
        >
          <ReceiptText className="size-3" aria-hidden="true" />
          {showDetails ? "隱藏收據" : `收據 #${receipt.receipt_id.slice(0, 8)}`}
        </button>
      </div>

      <div className="grid grid-cols-3 gap-2">
        {/* 金錢加成 */}
        <div className="rounded-lg bg-muted/60 p-2">
          <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
            <Coins className="size-3 text-legit" aria-hidden="true" />
            金錢 ({cashFactor} 倍)
          </div>
          <div className="mt-0.5 text-xs font-extrabold text-legit">
            +${formatMoney(cashFinal)}
          </div>
          {BigInt(cashBonus) > 0n && (
            <div className="text-[10px] text-muted-foreground">
              含加成 +${formatMoney(cashBonus)}
            </div>
          )}
        </div>

        {/* 養成經驗 */}
        <div className="rounded-lg bg-muted/60 p-2">
          <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
            <Zap className="size-3 text-primary" aria-hidden="true" />
            養成經驗 ({growthXpFactor} 倍)
          </div>
          <div className="mt-0.5 text-xs font-extrabold text-primary">
            +{formatMoney(growthXp)}
          </div>
          <div className="text-[10px] text-muted-foreground">核心階級經驗</div>
        </div>

        {/* 鍛造能量 */}
        <div className="rounded-lg bg-muted/60 p-2">
          <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
            <Hammer className="size-3 text-warning" aria-hidden="true" />
            鍛造能量 ({energyFactor} 倍)
          </div>
          <div className="mt-0.5 text-xs font-extrabold text-warning">
            +{formatMoney(energy)}
          </div>
          <div className="text-[10px] text-muted-foreground">工具突破素材</div>
        </div>
      </div>

      {showDetails && (
        <div className="mt-2.5 rounded-md border border-border bg-muted/30 p-2 text-[10px] text-muted-foreground">
          <div className="flex justify-between py-0.5">
            <span>收據編號</span>
            <span className="font-mono">{receipt.receipt_id}</span>
          </div>
          <div className="flex justify-between py-0.5">
            <span>數值模型版本</span>
            <span className="font-mono">{receipt.config_version}</span>
          </div>
          <div className="flex justify-between py-0.5">
            <span>固定完成獎勵</span>
            <span>${formatMoney(fixedCash)}，不套用倍率</span>
          </div>
          <div className="flex justify-between py-0.5">
            <span>核心等級</span>
            <span>
              Lv.{receipt.core_level_before} → Lv.{receipt.core_level_after}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
