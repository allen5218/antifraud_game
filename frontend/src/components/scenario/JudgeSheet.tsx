import {
  CheckCircle2,
  PauseCircle,
  ShieldAlert,
  ShieldCheck,
  X,
} from "lucide-react"

interface JudgeSheetProps {
  open: boolean
  onClose: () => void
  onJudge: (action: "report" | "comply" | "safe_exit" | "pause") => void
}

/** 聊天事件的處理選擇；線索只顯示玩家已在對話中取得的內容。 */
export function JudgeSheet({ open, onClose, onJudge }: JudgeSheetProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-t-2xl bg-background border-t border-border p-4 pb-6 shadow-2xl">
        <div className="flex items-center justify-between border-b border-border/40 pb-2.5 mb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-100">
              這件事要怎麼處理？
            </h3>
            <p className="text-xs text-muted-foreground">
              回想聊天與查證中已取得的資料，再替朋友做決定。
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1 text-muted-foreground hover:bg-muted"
            aria-label="關閉"
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="mb-3.5 rounded-xl border border-slate-800 bg-slate-900/80 p-2.5 text-xs text-slate-300">
          選擇你現在要怎麼處理這件事；結案後才會揭曉事件背景。
        </div>

        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={() => onJudge("report")}
            data-testid="judge-action-report"
            className="flex items-center justify-center gap-2 rounded-xl border border-rose-500/40 bg-rose-500/10 py-2.5 text-xs font-bold text-rose-300 hover:bg-rose-500/20 transition-colors"
          >
            <ShieldAlert className="size-4 text-rose-400" />
            <span>認為是詐騙，停止並通報</span>
          </button>
          <button
            type="button"
            onClick={() => onJudge("safe_exit")}
            data-testid="judge-action-safe-exit"
            className="flex items-center justify-center gap-2 rounded-xl border border-amber-500/40 bg-amber-500/10 py-2.5 text-xs font-bold text-amber-300 hover:bg-amber-500/20 transition-colors"
          >
            <ShieldCheck className="size-4 text-amber-400" />
            <span>先不辦理，結束這件事</span>
          </button>
          <button
            type="button"
            onClick={() => onJudge("pause")}
            data-testid="judge-action-pause"
            className="flex items-center justify-center gap-2 rounded-xl border border-sky-500/40 bg-sky-500/10 py-2.5 text-xs font-bold text-sky-300 hover:bg-sky-500/20 transition-colors"
          >
            <PauseCircle className="size-4 text-sky-400" />
            <span>稍後再聊（保留進度，不結案）</span>
          </button>
          <button
            type="button"
            onClick={() => onJudge("comply")}
            data-testid="judge-action-comply"
            className="flex items-center justify-center gap-2 rounded-xl border border-emerald-500/40 bg-emerald-500/10 py-2.5 text-xs font-bold text-emerald-300 hover:bg-emerald-500/20 transition-colors"
          >
            <CheckCircle2 className="size-4 text-emerald-400" />
            <span>確認後協助辦理</span>
          </button>
          <button
            type="button"
            onClick={onClose}
            className="mt-1 rounded-xl py-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            返回對話再思考
          </button>
        </div>
      </div>
    </div>
  )
}
