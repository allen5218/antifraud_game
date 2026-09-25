import { CircleCheck, CircleX } from "lucide-react"
import type { QuizWeaknessDetail } from "@/client"

interface Props {
  correct: boolean
  explanation: string
  weaknessDetails: QuizWeaknessDetail[]
}

/**
 * 滑卡作答後的回饋。
 *
 * 原本寫死 bg-green-50 / bg-red-50,在深色 App 裡是一塊突兀的淺色卡。
 * 改用主題的 legit / scam 語意色(淡底 + 同色邊框),深淺兩種配色都成立。
 */
export function SwipeFeedback({
  correct,
  explanation,
  weaknessDetails,
}: Props) {
  const Icon = correct ? CircleCheck : CircleX
  return (
    <div
      className={`rounded-xl border p-3 text-xs ${
        correct ? "border-legit/40 bg-legit/10" : "border-scam/40 bg-scam/10"
      }`}
    >
      <div
        className={`flex items-center gap-1.5 text-sm font-bold ${correct ? "text-legit" : "text-scam"}`}
      >
        <Icon aria-hidden className="size-4" />
        {correct ? "答對了！" : "答錯了"}
      </div>
      <p className="mt-1.5 leading-relaxed">{explanation}</p>
      {weaknessDetails.length > 0 && (
        <div className="mt-2 grid gap-1.5">
          {weaknessDetails.map((detail) => (
            <span key={detail.tag} className="rounded-lg bg-card px-2.5 py-2">
              <span className="block text-[11px] font-bold">
                {detail.label}
              </span>
              <span className="mt-0.5 block text-[11px] leading-relaxed text-muted-foreground">
                {detail.suggestion}
              </span>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
