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
    status.chapters.find((c) => c.is_current) ??
    status.chapters[status.chapters.length - 1]
  const multiplierPercent = Math.round((status.income_multiplier - 1) * 100)

  return (
    <div className="mb-3 space-y-2">
      {/* 創業補助領取橫幅（完成第 1 章且未領取時顯示） */}
      {status.can_claim_starter_grant && (
        <div className="flex items-center justify-between rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 p-3 text-white shadow-xs">
          <div>
            <div className="text-xs font-bold">🎉 完成第 1 章入門里程碑！</div>
            <div className="text-[10px] opacity-90">
              立即領取首期創業扶助金 7,000 元
            </div>
          </div>
          <Button
            size="sm"
            disabled={claimM.isPending}
            onClick={() => claimM.mutate()}
            className="bg-white text-xs font-bold text-amber-900 hover:bg-white/90"
          >
            {claimM.isPending ? "領取中…" : "領取 7,000 💰"}
          </Button>
        </div>
      )}

      {/* 主章節進度卡片 */}
      <div className="rounded-2xl border bg-gradient-to-br from-primary/5 via-card to-background p-4">
        <div className="flex items-center justify-between">
          <span className="rounded-md bg-primary/10 px-2 py-0.5 text-[10px] font-bold text-primary">
            訓練主線進度
          </span>
          <span className="text-xs font-semibold text-muted-foreground">
            已完成 {status.completed_chapters} / 5 章
          </span>
        </div>

        <div className="mt-2 font-bold text-foreground">
          {currentChapter?.title ?? "全章節已通關"}
        </div>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
          {currentChapter?.description}
        </p>

        {/* 晉級條件檢核 */}
        {currentChapter && !currentChapter.is_completed && (
          <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center justify-between rounded-xl border bg-card p-2">
              <span className="text-muted-foreground">快測題組訓練</span>
              {currentChapter.quiz_completed ? (
                <span className="font-bold text-green-600">✓ 已達成</span>
              ) : (
                <Link
                  to="/quick/quiz"
                  className="font-bold text-primary hover:underline"
                >
                  去訓練 ›
                </Link>
              )}
            </div>
            <div className="flex items-center justify-between rounded-xl border bg-card p-2">
              <span className="text-muted-foreground">情境查證通關</span>
              {currentChapter.scenario_completed ? (
                <span className="font-bold text-green-600">✓ 已達成</span>
              ) : (
                <Link
                  to="/scenarios"
                  className="font-bold text-primary hover:underline"
                >
                  去查證 ›
                </Link>
              )}
            </div>
          </div>
        )}

        {/* 倍率資訊列 */}
        <div className="mt-3 flex items-center justify-between border-t border-border/60 pt-2 text-[11px] text-muted-foreground">
          <span>⚡ 當前收益加成</span>
          <span className="font-bold text-primary">
            +{multiplierPercent}% (x{status.income_multiplier.toFixed(2)})
          </span>
        </div>
      </div>
    </div>
  )
}
