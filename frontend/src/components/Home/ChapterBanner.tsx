import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { CheckCircle2, Circle } from "lucide-react"
import { EconomyService } from "@/client"

const MOCK_CHAPTERS = {
  completed_chapters: 1,
  income_multiplier: 1.15,
  can_claim_starter_grant: true,
  chapters: [
    {
      chapter_number: 1,
      title: "第 1 章：初出茅廬防詐手冊",
      description: "完成一次題組訓練與一次情境查證，掌握基本紅旗辨識。",
      is_current: true,
      is_completed: false,
      quiz_completed: true,
      scenario_completed: false,
    },
    {
      chapter_number: 2,
      title: "第 2 章：資產保護與交易核對",
      description: "學習在購屋與二手車交易中核對身分與授權，防止資產損害。",
      is_current: false,
      is_completed: false,
      quiz_completed: false,
      scenario_completed: false,
    },
  ],
}

export function ChapterBanner() {
  const { data: status, isPending } = useQuery({
    queryKey: ["economy", "chapters"],
    queryFn: async () => {
      try {
        return await EconomyService.getChapters()
      } catch {
        return MOCK_CHAPTERS as any
      }
    },
  })

  if (isPending || !status) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-center text-xs text-slate-400">
        章節進度載入中...
      </div>
    )
  }

  const currentChapter =
    status.chapters.find((c: { is_current: boolean }) => c.is_current) ??
    status.chapters[status.chapters.length - 1]
  const multiplierPercent = Math.round((status.income_multiplier - 1) * 100)

  return (
    <div className="rounded-2xl border-[1.5px] border-white/25 bg-slate-900/90 p-3.5 glow-card backdrop-blur-xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-[10px] font-bold text-emerald-300">
            主線 CH.{currentChapter?.chapter_number ?? 1}
          </span>
          <span className="text-xs font-bold text-white">
            {currentChapter?.title?.replace(/^第 \d+ 章：/, "") ?? "初出茅廬"}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-xs">
          <span className="text-[10px] font-mono text-slate-400">
            {status.completed_chapters}/5 章
          </span>
          <span className="rounded-full border border-white/20 bg-white/10 px-2 py-0.5 text-[10px] font-mono font-bold text-emerald-300 glow-badge">
            +{multiplierPercent}%
          </span>
        </div>
      </div>

      {/* 晉級條件檢核 */}
      {currentChapter && !currentChapter.is_completed && (
        <div className="mt-2.5 grid grid-cols-2 gap-2">
          <div className="flex items-center justify-between rounded-xl border-[1.5px] border-white/20 bg-slate-800/60 px-3 py-2 glow-subcard">
            <div className="flex items-center gap-2 min-w-0">
              {currentChapter.quiz_completed ? (
                <CheckCircle2 className="size-3.5 text-emerald-400 shrink-0" />
              ) : (
                <Circle className="size-3.5 text-slate-500 shrink-0" />
              )}
              <span className="text-xs font-semibold text-slate-200 truncate">
                題組訓練
              </span>
            </div>
            {currentChapter.quiz_completed ? (
              <span className="text-[10px] font-bold text-emerald-400 shrink-0">
                完成
              </span>
            ) : (
              <Link
                to="/quick/quiz"
                className="rounded-lg border border-white/30 bg-white/15 px-2 py-0.5 text-[10px] font-bold text-white hover:bg-white/25 shrink-0"
              >
                前往
              </Link>
            )}
          </div>

          <div className="flex items-center justify-between rounded-xl border-[1.5px] border-white/20 bg-slate-800/60 px-3 py-2 glow-subcard">
            <div className="flex items-center gap-2 min-w-0">
              {currentChapter.scenario_completed ? (
                <CheckCircle2 className="size-3.5 text-emerald-400 shrink-0" />
              ) : (
                <Circle className="size-3.5 text-slate-500 shrink-0" />
              )}
              <span className="text-xs font-semibold text-slate-200 truncate">
                情境查證
              </span>
            </div>
            {currentChapter.scenario_completed ? (
              <span className="text-[10px] font-bold text-emerald-400 shrink-0">
                完成
              </span>
            ) : (
              <Link
                to="/scenarios"
                className="rounded-lg border border-white/20 bg-white/10 px-2 py-0.5 text-[10px] font-bold text-white hover:bg-white/20 shrink-0"
              >
                前往
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
