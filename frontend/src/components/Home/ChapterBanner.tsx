import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
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
    <div className="space-y-3">

      {/* 主章節進度卡片 */}
      <div className="relative overflow-hidden rounded-2xl border border-white/20 bg-slate-900/80 p-4 shadow-[0_0_20px_rgba(255,255,255,0.06)] backdrop-blur-xl transition-all hover:border-white/30">
        <div className="relative">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="flex h-6 items-center rounded-full border border-white/20 bg-white/5 px-2.5 text-[10px] font-bold uppercase tracking-wider text-slate-300">
                主線任務
              </span>
              <span className="text-[10px] font-mono font-semibold text-slate-400">
                CH.{currentChapter?.chapter_number ?? 1}
              </span>
            </div>
            <span className="text-xs font-mono font-semibold text-slate-300 bg-white/5 border border-white/15 px-2.5 py-0.5 rounded-full">
              通關 {status.completed_chapters} / 5 章
            </span>
          </div>

          <div className="mt-2.5 text-base font-bold tracking-wide text-white">
            {currentChapter?.title ?? "全章節已通關"}
          </div>
          <p className="mt-1 text-xs leading-relaxed text-slate-400 font-medium">
            {currentChapter?.description}
          </p>

          {/* 晉級條件檢核雙卡 */}
          {currentChapter && !currentChapter.is_completed && (
            <div className="mt-3.5 grid grid-cols-2 gap-2 text-xs">
              <div className="flex flex-col justify-between rounded-xl border border-white/10 bg-white/5 p-3 backdrop-blur-md transition-all hover:border-white/20">
                <div className="text-[10px] font-semibold text-slate-400 flex items-center justify-between">
                  <span>測驗刷題</span>
                  {currentChapter.quiz_completed && (
                    <span className="text-emerald-400 font-bold">已完成</span>
                  )}
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span className="font-semibold text-slate-200">題組訓練</span>
                  {currentChapter.quiz_completed ? (
                    <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]" />
                  ) : (
                    <Link
                      to="/quick/quiz"
                      className="inline-flex items-center rounded-lg border border-white/25 bg-white/10 px-2.5 py-1 text-[11px] font-bold text-white shadow-sm hover:bg-white/20"
                    >
                      去訓練
                    </Link>
                  )}
                </div>
              </div>

              <div className="flex flex-col justify-between rounded-xl border border-white/10 bg-white/5 p-3 backdrop-blur-md transition-all hover:border-white/20">
                <div className="text-[10px] font-semibold text-slate-400 flex items-center justify-between">
                  <span>真實偵查</span>
                  {currentChapter.scenario_completed && (
                    <span className="text-emerald-400 font-bold">已完成</span>
                  )}
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span className="font-semibold text-slate-200">情境查證</span>
                  {currentChapter.scenario_completed ? (
                    <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]" />
                  ) : (
                    <Link
                      to="/scenarios"
                      className="inline-flex items-center rounded-lg border border-white/25 bg-white/10 px-2.5 py-1 text-[11px] font-bold text-white shadow-sm hover:bg-white/20"
                    >
                      去查證
                    </Link>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* 倍率資訊列 */}
          <div className="mt-3.5 flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs">
            <span className="text-slate-400 font-medium">
              當前全域收益加成
            </span>
            <span className="font-mono font-bold text-white text-sm">
              +{multiplierPercent}% <span className="text-[10px] text-slate-500">(x{status.income_multiplier.toFixed(2)})</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
