interface JudgeSheetProps {
  open: boolean
  onClose: () => void
  onJudge: (action: "report" | "comply") => void
}

/** 右上「⚖️ 下判斷」彈出的終局選擇 sheet */
export function JudgeSheet({ open, onClose, onJudge }: JudgeSheetProps) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40">
      <div className="w-full max-w-md rounded-t-2xl bg-background p-4 pb-6">
        <h3 className="mb-1 text-center text-sm font-bold">你的判斷是?</h3>
        <p className="mb-4 text-center text-xs text-muted-foreground">
          判斷是終局:對了有獎勵,錯了會付出代價
        </p>
        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={() => onJudge("report")}
            className="rounded-xl border border-red-200 py-3 text-sm font-bold text-red-600"
          >
            🚩 我覺得是詐騙(檢舉/封鎖)
          </button>
          <button
            type="button"
            onClick={() => onJudge("comply")}
            className="rounded-xl border border-green-200 py-3 text-sm font-bold text-green-600"
          >
            ✅ 我選擇信任(照對方說的做)
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl py-2 text-xs text-muted-foreground"
          >
            再想想
          </button>
        </div>
      </div>
    </div>
  )
}
