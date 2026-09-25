import { Flag, Handshake } from "lucide-react"
import { useDialogFocus } from "@/hooks/useDialogFocus"

interface JudgeSheetProps {
  open: boolean
  onClose: () => void
  onJudge: (action: "report" | "comply") => void
}

/** 右上「下判斷」彈出的終局選擇 */
export function JudgeSheet({ open, onClose, onJudge }: JudgeSheetProps) {
  const dialogRef = useDialogFocus<HTMLDivElement>(open)
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50">
      <div
        ref={dialogRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="judge-sheet-title"
        className="w-full max-w-md rounded-t-2xl border-t border-border bg-card p-4 pb-6 outline-none"
      >
        <h3
          id="judge-sheet-title"
          className="mb-1 text-center text-sm font-bold"
        >
          你的判斷是？
        </h3>
        <p className="mb-4 text-center text-xs text-muted-foreground">
          判斷後這段對話就結束：判斷對了有獎勵，錯了要付出代價
        </p>
        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={() => onJudge("report")}
            className="flex items-center justify-center gap-1.5 rounded-xl border border-scam/50 bg-scam/10 py-3 text-sm font-bold text-scam"
          >
            <Flag aria-hidden className="size-4" />
            這是詐騙（檢舉並封鎖）
          </button>
          <button
            type="button"
            onClick={() => onJudge("comply")}
            className="flex items-center justify-center gap-1.5 rounded-xl border border-legit/50 bg-legit/10 py-3 text-sm font-bold text-legit"
          >
            <Handshake aria-hidden className="size-4" />
            我相信對方（照對方說的做）
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
