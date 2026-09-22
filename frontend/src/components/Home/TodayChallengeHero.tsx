import { Link } from "@tanstack/react-router"
import { ChevronRight, Flame, ShieldCheck } from "lucide-react"
import { useEconomyMe } from "@/hooks/useEconomy"

/**
 * 首頁主要行動卡。
 *
 * 原本這裡是一張寫死的「今日挑戰 · 投資詐欺 · 5 題 · +500💰」,而且是 plain div
 * ——點下去沒有任何反應,數字也全是假的。沒有「今日挑戰」這個 API,與其擺一張
 * 假卡片,不如把它換成真的入口:連到題組訓練,並且只顯示 economy/me 真的有回傳的值。
 */
export function TodayChallengeHero() {
  const { data } = useEconomyMe()
  const streakDays = data?.streak_days ?? 0

  return (
    <Link
      to="/quick/quiz"
      data-testid="home-hero"
      className="mb-3 block overflow-hidden rounded-2xl bg-gradient-to-br from-primary to-accent p-4 text-primary-foreground shadow-lg transition hover:brightness-110 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
    >
      <span className="mb-2 inline-flex items-center gap-1 rounded-full bg-white/20 px-2 py-0.5 text-[10px] font-medium">
        <ShieldCheck aria-hidden className="size-3" />
        開始練習
      </span>
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="font-bold">題組訓練</div>
          <div className="text-[11px] opacity-90">
            判斷真假、辨識話術、學會查證
          </div>
        </div>
        <ChevronRight aria-hidden className="size-5 shrink-0 opacity-80" />
      </div>
      {streakDays > 0 && (
        <div className="mt-2 inline-flex items-center gap-1 text-[11px] opacity-90">
          <Flame aria-hidden className="size-3.5" />
          連續 {streakDays} 天 · 今天也別斷
        </div>
      )}
    </Link>
  )
}
