import type { QuizWeaknessDetail } from "@/client"

interface Props {
  correct: boolean
  explanation: string
  weaknessDetails: QuizWeaknessDetail[]
}

export function SwipeFeedback({
  correct,
  explanation,
  weaknessDetails,
}: Props) {
  return (
    <div
      className={`rounded-2xl border p-4 text-xs shadow-lg backdrop-blur-xl ${
        correct
          ? "border-emerald-500/30 bg-emerald-950/40 text-slate-100"
          : "border-red-500/30 bg-red-950/40 text-slate-100"
      }`}
    >
      <div
        className={`text-sm font-bold flex items-center gap-1.5 ${
          correct ? "text-emerald-400" : "text-red-400"
        }`}
      >
        <span>{correct ? "辨識正確" : "判斷失準"}</span>
      </div>
      <p className="mt-1 text-muted-foreground">{explanation}</p>
      {weaknessDetails.length > 0 && (
        <div className="mt-2 grid gap-1.5">
          {weaknessDetails.map((detail) => (
            <span key={detail.tag} className="rounded-lg bg-muted px-2 py-1.5">
              <span className="block text-[10px] font-bold">
                {detail.label}
              </span>
              <span className="mt-0.5 block text-[10px] text-muted-foreground">
                {detail.suggestion}
              </span>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
