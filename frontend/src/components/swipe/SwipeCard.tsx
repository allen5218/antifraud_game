import { motion, type PanInfo } from "framer-motion"
import { Check, MessageSquare, Shield, X } from "lucide-react"

interface Card {
  id: string
  scenario?: string
  scenario_text?: string
  sender_avatar?: string
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

  const text = card.scenario_text ?? card.scenario ?? "載入訊息內容中..."

  return (
    <div className="space-y-6">
      {/* 3D Stacked Card Visual Container */}
      <div className="relative group">
        <div className="absolute -inset-1 bg-gradient-to-r from-emerald-500 via-sky-500 to-indigo-500 rounded-3xl blur-md opacity-25 group-hover:opacity-50 transition duration-500" />
        <motion.div
          drag="x"
          dragConstraints={{ left: 0, right: 0 }}
          onDragEnd={handleDragEnd}
          whileDrag={{ scale: 1.03, rotate: 2 }}
          className="relative rounded-3xl border border-slate-700/60 bg-gradient-to-b from-slate-900 via-slate-900/90 to-slate-950 p-6 shadow-2xl backdrop-blur-xl cursor-grab active:cursor-grabbing flex flex-col justify-between min-h-[260px]"
        >
          {/* Card Top Badge */}
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
            <div className="flex items-center gap-2">
              <span className="p-1.5 bg-slate-800/80 rounded-xl border border-slate-700/80 flex items-center justify-center">
                <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
              </span>
              <span className="text-xs font-bold text-emerald-400 font-mono tracking-wider uppercase">
                165 快篩
              </span>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800/80 border border-slate-700/80 text-slate-400 font-mono">
              把關中
            </span>
          </div>

          {/* Card Main Scenario Text */}
          <div className="my-4">
            <p className="text-sm sm:text-base leading-relaxed text-slate-100 font-medium tracking-wide">
              {text}
            </p>
          </div>

          {/* Card Drag Direction Guide Indicator */}
          <div className="flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/60 pt-2.5">
            <span className="text-red-400 font-semibold flex items-center gap-1">
              ← 左滑：詐騙
            </span>
            <span className="text-emerald-400 font-semibold flex items-center gap-1">
              右滑：正常 →
            </span>
          </div>
        </motion.div>
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-3 gap-2.5">
        <button
          type="button"
          onClick={() => onJudge("scam")}
          className="py-2.5 px-2 rounded-2xl border border-red-500/30 bg-red-950/40 hover:bg-red-900/60 text-red-300 font-bold text-xs shadow-lg transition-all hover:scale-105 active:scale-95 flex flex-col items-center justify-center gap-1"
        >
          <X className="w-4 h-4 text-red-400" />
          <span>詐騙</span>
        </button>

        <button
          type="button"
          aria-label="避險 (略過)"
          onClick={() => onJudge("skip")}
          className="py-2.5 px-2 rounded-2xl border border-amber-500/30 bg-amber-950/40 hover:bg-amber-900/60 text-amber-300 font-bold text-xs shadow-lg transition-all hover:scale-105 active:scale-95 flex flex-col items-center justify-center gap-1"
        >
          <Shield className="w-4 h-4 text-amber-400" />
          <span>避險</span>
        </button>

        <button
          type="button"
          onClick={() => onJudge("legit")}
          className="py-2.5 px-2 rounded-2xl border border-emerald-500/30 bg-emerald-950/40 hover:bg-emerald-900/60 text-emerald-300 font-bold text-xs shadow-lg transition-all hover:scale-105 active:scale-95 flex flex-col items-center justify-center gap-1"
        >
          <Check className="w-4 h-4 text-emerald-400" />
          <span>正常</span>
        </button>
      </div>
    </div>
  )
}
