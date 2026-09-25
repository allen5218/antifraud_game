import { CircleCheck, CircleX } from "lucide-react"
import { OUTCOME_BADGES } from "./labels"

/** 情境結局的小徽章(收件匣列、對話頁頂列)。 */
export function OutcomeBadge({
  outcome,
  className = "",
}: {
  outcome: string
  className?: string
}) {
  const badge = OUTCOME_BADGES[outcome]
  if (!badge) return null
  const win = badge.tone === "win"
  const Icon = win ? CircleCheck : CircleX
  return (
    <span
      className={`flex items-center gap-1 font-bold ${win ? "text-legit" : "text-scam"} ${className}`}
    >
      <Icon aria-hidden className="size-3.5" />
      {badge.label}
    </span>
  )
}
