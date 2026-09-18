import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { EconomyService } from "@/client"
import { Button } from "@/components/ui/button"

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
  const qc = useQueryClient()
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

  const claimM = useMutation({
    mutationFn: () => EconomyService.postClaimStarterGrant(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["economy"] })
    },
  })

  if (isPending || !status) {
    return (
      <div className="mb-3 rounded-2xl bg-muted p-4 text-center text-xs text-muted-foreground">
        章節進度載入中…
      </div>
    )
  }

  const currentChapter =
    status.chapters.find((c: { is_current: boolean }) => c.is_current) ??
    status.chapters[status.chapters.length - 1]
  const multiplierPercent = Math.round((status.income_multiplier - 1) * 100)

  return (
    <div className="space-y-3">
      {/* 創業補助領取橫幅（完成第 1 章且未領取時顯示） */}
      {status.can_claim_starter_grant && (
        <div className="relative overflow-hidden rounded-2xl border border-amber-400/50 bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 p-4 text-white shadow-[0_0_25px_rgba(245,158,11,0.4)] animate-pulse">
          <div className="absolute right-0 top-0 h-32 w-32 translate-x-8 -translate-y-8 rounded-full bg-white/20 blur-2xl" />
          <div className="relative flex items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-1.5 text-xs font-black tracking-wider text-amber-100">
                <span>🎉</span> 首期創業扶助金解鎖！
              </div>
              <div className="mt-0.5 text-sm font-extrabold text-white">
                領取第 1 章通關獎勵 <span className="text-yellow-300 font-mono text-base">7,000 元</span>
              </div>
            </div>
            <Button
              size="sm"
              disabled={claimM.isPending}
              onClick={() => claimM.mutate()}
              className="shrink-0 rounded-xl bg-slate-950 px-4 py-2.5 text-xs font-black text-amber-300 border border-amber-400/40 shadow-lg hover:bg-slate-900 active:scale-95"
            >
              {claimM.isPending ? "領取中..." : "🎁 立即領取"}
            </Button>
          </div>
        </div>
      )}

      {/* 主章節進度卡片 */}
      <div className="relative overflow-hidden rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/80 via-slate-900 to-slate-950 p-4 shadow-[0_4px_25px_rgba(0,0,0,0.5)] backdrop-blur-xl">
        {/* Glow Decorator */}
        <div className="absolute -left-10 -top-10 h-32 w-32 rounded-full bg-indigo-500/10 blur-2xl" />
        <div className="absolute -right-10 -bottom-10 h-32 w-32 rounded-full bg-emerald-500/10 blur-2xl" />

        <div className="relative">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="flex h-6 items-center rounded-full border border-indigo-400/30 bg-indigo-500/20 px-2.5 text-[10px] font-black uppercase tracking-wider text-indigo-300">
                🎯 主線任務
              </span>
              <span className="text-[10px] font-mono font-bold text-slate-400">
                CH.{currentChapter?.chapter_number ?? 1}
              </span>
            </div>
            <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 rounded-full">
              通關 {status.completed_chapters} / 5 章
            </span>
          </div>

          <div className="mt-2.5 text-base font-black tracking-wide text-slate-100 flex items-center gap-2">
            <span>{currentChapter?.title ?? "全章節已通關"}</span>
          </div>
          <p className="mt-1 text-xs leading-relaxed text-slate-400 font-medium">
            {currentChapter?.description}
          </p>

          {/* 晉級條件檢核雙卡 */}
          {currentChapter && !currentChapter.is_completed && (
            <div className="mt-3.5 grid grid-cols-2 gap-2 text-xs">
              <div className="flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/90 p-3 backdrop-blur-md transition-all hover:border-slate-700">
                <div className="text-[10px] font-bold text-slate-400 flex items-center justify-between">
                  <span>測驗刷題</span>
                  {currentChapter.quiz_completed && (
                    <span className="text-emerald-400 font-extrabold">✓ 已完成</span>
                  )}
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span className="font-bold text-slate-200">題组訓練</span>
                  {currentChapter.quiz_completed ? (
                    <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" />
                  ) : (
                    <Link
                      to="/quick/quiz"
                      className="inline-flex items-center gap-0.5 rounded-lg bg-indigo-600/90 border border-indigo-400/40 px-2.5 py-1 text-[11px] font-black text-white shadow-md hover:bg-indigo-500"
                    >
                      去訓練 ⚡
                    </Link>
                  )}
                </div>
              </div>

              <div className="flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/90 p-3 backdrop-blur-md transition-all hover:border-slate-700">
                <div className="text-[10px] font-bold text-slate-400 flex items-center justify-between">
                  <span>真實偵查</span>
                  {currentChapter.scenario_completed && (
                    <span className="text-emerald-400 font-extrabold">✓ 已完成</span>
                  )}
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span className="font-bold text-slate-200">情境查證</span>
                  {currentChapter.scenario_completed ? (
                    <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" />
                  ) : (
                    <Link
                      to="/scenarios"
                      className="inline-flex items-center gap-0.5 rounded-lg bg-emerald-600/90 border border-emerald-400/40 px-2.5 py-1 text-[11px] font-black text-white shadow-md hover:bg-emerald-500"
                    >
                      去查證 🔍
                    </Link>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* 倍率資訊列 */}
          <div className="mt-3.5 flex items-center justify-between rounded-xl border border-slate-800/80 bg-slate-950/60 px-3 py-2 text-xs">
            <span className="flex items-center gap-1.5 text-slate-400 font-medium">
              <span>⚡</span> 當前全域收益加成
            </span>
            <span className="font-mono font-black text-amber-400 text-sm">
              +{multiplierPercent}% <span className="text-[10px] text-slate-500">(x{status.income_multiplier.toFixed(2)})</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
