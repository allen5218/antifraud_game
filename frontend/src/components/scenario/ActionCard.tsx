import { Hand } from "lucide-react"

interface ActionCardProps {
  text: string
  onComply: () => void
  onRefuse: () => void
  disabled: boolean
  /** 回合用盡時只鎖「拒絕」(=送訊息);「照做」(=下判斷)仍可用 */
  refuseDisabled?: boolean
}

/**
 * 對方提出具體要求(匯款、個資、下載 App…)時內嵌在聊天裡的行動卡;
 * 照做=終局 comply,拒絕=繼續聊。
 *
 * 顏色刻意中性:正常角色在正式流程裡也會提出要求,照做有時才是對的。
 * 原本「照做」是紅色按鈕、整張卡是橘色警示,等於替玩家先下了判斷。
 */
export function ActionCard({
  text,
  onComply,
  onRefuse,
  disabled,
  refuseDisabled = false,
}: ActionCardProps) {
  return (
    <div className="rounded-xl border border-primary/40 bg-card p-3">
      <p className="mb-2 flex gap-1.5 text-xs font-semibold">
        <Hand aria-hidden className="mt-px size-3.5 shrink-0 text-primary" />
        <span>對方要求：{text}</span>
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          disabled={disabled}
          onClick={onComply}
          className="flex-1 rounded-lg bg-primary py-1.5 text-xs font-bold text-primary-foreground disabled:opacity-50"
        >
          照做
        </button>
        <button
          type="button"
          disabled={disabled || refuseDisabled}
          onClick={onRefuse}
          className="flex-1 rounded-lg border border-border bg-muted py-1.5 text-xs font-bold text-foreground disabled:opacity-50"
        >
          拒絕
        </button>
      </div>
    </div>
  )
}
