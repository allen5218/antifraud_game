interface ActionCardProps {
  text: string
  onComply: () => void
  onRefuse: () => void
  disabled: boolean
}

/** 對方提出具體要求(匯款/個資)時內嵌聊天流的行動卡;照做=終局 comply,拒絕=繼續聊 */
export function ActionCard({
  text,
  onComply,
  onRefuse,
  disabled,
}: ActionCardProps) {
  return (
    <div className="rounded-xl border border-orange-200 bg-orange-50 p-3 dark:border-orange-900 dark:bg-orange-950/40">
      <p className="mb-2 text-xs font-semibold text-orange-900 dark:text-orange-200">
        💸 對方要求:{text}
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          disabled={disabled}
          onClick={onComply}
          className="flex-1 rounded-lg bg-red-500 py-1.5 text-xs font-bold text-white disabled:opacity-50"
        >
          照做
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={onRefuse}
          className="flex-1 rounded-lg bg-muted py-1.5 text-xs font-bold text-foreground disabled:opacity-50"
        >
          拒絕
        </button>
      </div>
    </div>
  )
}
