import { motion, type PanInfo } from "framer-motion"

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
          className="flex-1 rounded-xl border border-red-300 bg-red-50 py-3 font-bold text-red-700"
        >
          ← 詐騙
        </button>
        <button
          type="button"
          onClick={() => onJudge(false)}
          className="flex-1 rounded-xl border border-green-300 bg-green-50 py-3 font-bold text-green-700"
        >
          正常 →
        </button>
      </div>
      <p className="mt-2 text-center text-[11px] text-muted-foreground">
        左滑＝詐騙 · 右滑＝正常
      </p>
    </div>
  )
}
