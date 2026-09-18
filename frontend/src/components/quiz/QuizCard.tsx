import type { QuizDeckResponse } from "@/client"
import { MatchQuestion } from "./MatchQuestion"
import { TacticsQuestion } from "./TacticsQuestion"
import { VerdictQuestion } from "./VerdictQuestion"
import { VerificationQuestion } from "./VerificationQuestion"

type QuizItem = QuizDeckResponse["items"][number]

export type QuizDraftAnswer =
  | { guess_is_scam: boolean }
  | { selected_option: string }
  | { selected_tags: string[] }
  | { pairs: Record<string, string> }

interface QuizCardProps {
  item: QuizItem
  index: number
  total: number
  onSubmit: (answer: QuizDraftAnswer) => void
  disabled: boolean
}

/** 混合題型分派器：每個題型自行管理送出前的草稿狀態。 */
export function QuizCard({
  item,
  index,
  total,
  onSubmit,
  disabled,
}: QuizCardProps) {
  switch (item.type) {
    case "verdict":
      return (
        <VerdictQuestion
          item={item}
          index={index}
          total={total}
          disabled={disabled}
          onSubmit={(guessIsScam) => onSubmit({ guess_is_scam: guessIsScam })}
        />
      )
    case "verification":
      return (
        <VerificationQuestion
          item={item}
          index={index}
          total={total}
          disabled={disabled}
          onSubmit={(selectedOption) =>
            onSubmit({ selected_option: selectedOption })
          }
        />
      )
    case "tactics":
      return (
        <TacticsQuestion
          item={item}
          index={index}
          total={total}
          disabled={disabled}
          onSubmit={(selectedTags) => onSubmit({ selected_tags: selectedTags })}
        />
      )
    case "match":
      return (
        <MatchQuestion
          item={item}
          index={index}
          total={total}
          disabled={disabled}
          onSubmit={(pairs) => onSubmit({ pairs })}
        />
      )
    default:
      return (
        <p className="py-12 text-center text-xs text-muted-foreground">
          無法顯示這道題目
        </p>
      )
  }
}
