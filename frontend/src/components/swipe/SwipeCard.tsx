import { motion, type PanInfo } from "framer-motion"
import { ArrowLeft, ArrowRight } from "lucide-react"

interface Card {
  id: string
  scenario: string
  source_label: string
  fraud_type: string
  difficulty: number
}

const THRESHOLD = 100

export function SwipeCard({
  card,
  onJudge,
}: {
  card: Card
  onJudge: (guessIsScam: boolean) => void
}) {
  const handleDragEnd = (_: unknown, info: PanInfo) => {
    if (info.offset.x < -THRESHOLD) onJudge(true)
    else if (info.offset.x > THRESHOLD) onJudge(false)
  }

  return (
    <div>
      <motion.div
        drag="x"
        dragConstraints={{ left: 0, right: 0 }}
        onDragEnd={handleDragEnd}
        className="rounded-2xl border bg-card p-5"
        whileDrag={{ scale: 1.02 }}
      >
        <div className="mb-2 text-xs text-muted-foreground">
          {card.source_label}
        </div>
        <p className="text-sm leading-relaxed">{card.scenario}</p>
      </motion.div>
      <div className="mt-4 flex gap-3">
        <button
          type="button"
          onClick={() => onJudge(true)}
          className="flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-scam/50 bg-scam/10 py-3 font-bold text-scam"
        >
          <ArrowLeft aria-hidden className="size-4" />
          詐騙
        </button>
        <button
          type="button"
          onClick={() => onJudge(false)}
          className="flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-legit/50 bg-legit/10 py-3 font-bold text-legit"
        >
          正常
          <ArrowRight aria-hidden className="size-4" />
        </button>
      </div>
      <p className="mt-2 text-center text-[11px] text-muted-foreground">
        往左滑是詐騙，往右滑是正常
      </p>
    </div>
  )
}
