import { Star } from "lucide-react"
import { fraudTypeLabel } from "@/lib/fraudTypes"

interface QuestionMetaProps {
  fraudType: string
  difficulty: number
  index: number
  total: number
}

/** 題目頂列:詐騙類型、難度、題號。是非、話術、查證三種題型共用。 */
export function QuestionMeta({
  fraudType,
  difficulty,
  index,
  total,
}: QuestionMetaProps) {
  return (
    <div className="flex items-center gap-2 px-4 pt-3 text-xs text-muted-foreground">
      <span className="rounded-md bg-primary/10 px-1.5 py-0.5 font-semibold text-primary">
        {fraudTypeLabel(fraudType)}
      </span>
      <span
        className="flex items-center gap-0.5 text-warning"
        role="img"
        aria-label={`難度 ${difficulty}`}
      >
        {Array.from({ length: difficulty }, (_, i) => (
          <Star key={i} aria-hidden className="size-3 fill-current" />
        ))}
      </span>
      <span className="ml-auto">
        {index + 1} / {total}
      </span>
    </div>
  )
}
