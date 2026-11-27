import { Coins, ReceiptText, Sparkles } from "lucide-react"
import { useState } from "react"
import type { RewardReceiptSchema } from "@/client"
import { formatMoney } from "@/utils/money"
import { formatFactor } from "@/utils/progressionDisplay"

interface RewardBreakdownProps {
  receipt?: RewardReceiptSchema | null
  className?: string
}

/** 練習獎勵明細：拿到的錢，以及信譽讓它多了多少（倍率在開局時鎖定） */
export function RewardBreakdown({
  receipt,
  className = "",
}: RewardBreakdownProps) {
  const [showDetails, setShowDetails] = useState(false)

  if (!receipt) return null

  const cashFinal = receipt.final?.cash_total ?? "0"
  const cashBonus = receipt.final?.cash_bonus ?? "0"
  const fixedCash = receipt.final?.fixed_cash ?? "0"
  const cashFactor = formatFactor(receipt.factors?.cash)

  return (
    <div
      className={`w-full rounded-xl border border-border bg-card p-3.5 text-left text-card-foreground shadow-xs ${className}`}
    >
      <div className="mb-2 flex items-center justify-between">
        <span className="flex items-center gap-1.5 text-xs font-bold text-muted-foreground">
          <Sparkles className="size-3.5" aria-hidden="true" />
          信譽加成
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

      <div className="rounded-lg bg-muted/60 p-2">
        <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
          <Coins className="size-3 text-legit" aria-hidden="true" />
          錢（{cashFactor} 倍）
        </div>
        <div className="mt-0.5 text-xs font-extrabold text-legit">
          +{formatMoney(cashFinal)} 元
        </div>
        {BigInt(cashBonus) > 0n && (
          <div className="text-[10px] text-muted-foreground">
            信譽多給 {formatMoney(cashBonus)} 元
          </div>
        )}
      </div>

      {showDetails && (
        <div className="mt-2.5 rounded-md border border-border bg-muted/30 p-2 text-[10px] text-muted-foreground">
          <div className="flex justify-between py-0.5">
            <span>收據編號</span>
            <span className="font-mono">{receipt.receipt_id}</span>
          </div>
          <div className="flex justify-between py-0.5">
            <span>數值版本</span>
            <span className="font-mono">{receipt.config_version}</span>
          </div>
          <div className="flex justify-between py-0.5">
            <span>固定完成獎勵</span>
            <span>{formatMoney(fixedCash)} 元，不乘信譽</span>
          </div>
        </div>
      )}
    </div>
  )
}
