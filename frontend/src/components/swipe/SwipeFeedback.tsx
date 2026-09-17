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
      className={`rounded-xl border p-3 text-xs ${
        correct ? "border-green-300 bg-green-50" : "border-red-300 bg-red-50"
      }`}
    >
      <div
        className={`font-bold ${correct ? "text-green-700" : "text-red-700"}`}
      >
        {correct ? "答對！" : "答錯"}
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
