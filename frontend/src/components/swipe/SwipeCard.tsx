import { motion, type PanInfo } from "framer-motion"

interface Card {
  id: string
  scenario: string
}

const THRESHOLD = 100

export function SwipeCard({
  card,
  onJudge,
}: {
  card: Card
  onJudge: (action: "scam" | "legit" | "skip") => void
}) {
  const handleDragEnd = (_: unknown, info: PanInfo) => {
    if (info.offset.x < -THRESHOLD) onJudge("scam")
    else if (info.offset.x > THRESHOLD) onJudge("legit")
  }

  return (
    <div>
      <motion.div
        drag="x"
        dragConstraints={{ left: 0, right: 0 }}
        onDragEnd={handleDragEnd}
        className="rounded-2xl border bg-card p-5 shadow-xs"
        whileDrag={{ scale: 1.02 }}
      >
        <div className="mb-2 text-xs font-semibold text-primary">
          快速情境滑卡
        </div>
        <p className="text-sm leading-relaxed">{card.scenario}</p>
      </motion.div>
      <div className="mt-4 flex items-center gap-2">
        <button
          type="button"
          onClick={() => onJudge("scam")}
          className="flex-1 rounded-xl border border-red-300 bg-red-50 py-3 text-xs font-bold text-red-700 hover:bg-red-100 dark:border-red-900 dark:bg-red-950 dark:text-red-300"
        >
          ← 詐騙
        </button>
        <button
          type="button"
          onClick={() => onJudge("skip")}
          className="flex-1 rounded-xl border border-amber-300 bg-amber-50 py-3 text-xs font-bold text-amber-700 hover:bg-amber-100 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-300"
        >
          資訊不足略過
        </button>
        <button
          type="button"
          onClick={() => onJudge("legit")}
          className="flex-1 rounded-xl border border-green-300 bg-green-50 py-3 text-xs font-bold text-green-700 hover:bg-green-100 dark:border-green-900 dark:bg-green-950 dark:text-green-300"
        >
          正常 →
        </button>
      </div>
      <p className="mt-2 text-center text-[11px] text-muted-foreground">
        左滑＝詐騙 · 中鍵＝安全避險 · 右滑＝正常
      </p>
    </div>
  )
}
