import type { QuizAnswerResponse } from "@/client"

interface QuizRevealProps {
  result: QuizAnswerResponse
  onNext: () => void
  isLast: boolean
}

/** 單題揭曉:對錯 + 真相 + 紅旗教學 + 溯源 */
export function QuizReveal({ result, onNext, isLast }: QuizRevealProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40">
      <div className="max-h-[85vh] w-full max-w-md overflow-y-auto rounded-t-2xl bg-background p-4 pb-6">
        <h3
          className={`text-center text-lg font-extrabold ${result.correct ? "text-green-600" : "text-red-600"}`}
        >
          {result.correct ? "✓ 答對了!" : "✗ 答錯了…"}
        </h3>
        <p className="mt-1 text-center text-xs text-muted-foreground">
          正解:這則{result.is_scam ? "是詐騙" : "是正當內容"}
        </p>
        <p className="mt-3 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
          {result.is_scam ? "紅旗解析" : "正當訊號"}
        </p>
        <ul className="mt-1.5 flex flex-col gap-1.5">
          {result.red_flags.map((f) => (
            <li key={f.text} className="text-xs leading-snug">
              {f.tag ? "🚩" : "✅"} {f.text}
              {f.tag && (
                <span className="ml-1 rounded bg-red-50 px-1 py-0.5 text-[9px] font-bold text-red-600 dark:bg-red-950">
                  {f.tag}
                </span>
              )}
            </li>
          ))}
        </ul>
        <p className="mt-3 rounded-lg bg-muted px-3 py-2 text-[11px] text-muted-foreground">
          📎 {result.provenance}
        </p>
        <button
          type="button"
          onClick={onNext}
          className="mt-3 w-full rounded-xl bg-foreground py-2.5 text-sm font-bold text-background"
        >
          {isLast ? "看結算 ›" : "下一題 ›"}
        </button>
      </div>
    </div>
  )
}
