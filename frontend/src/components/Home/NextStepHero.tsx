import { Link } from "@tanstack/react-router"
import { ChevronRight, Flame, Target } from "lucide-react"
import type { ReactNode } from "react"
import { gateRemaining } from "@/components/exam/exam"
import { useEconomyMe } from "@/hooks/useEconomy"
import { usePracticeProfile } from "@/hooks/usePractice"
import { fraudTypeLabel } from "@/lib/fraudTypes"

/**
 * 首頁主要行動卡：依練習重點告訴玩家下一步。
 * 沒做前測先做前測；檢測沒過顯示補考還差多少；平常寫出這一輪加強哪一類。
 * 五類比例的長條留在「我」頁的 PracticeFocusCard。
 */
export function NextStepHero() {
  const { data, isError } = usePracticeProfile()
  const streakDays = useEconomyMe().data?.streak_days ?? 0

  if (!data && !isError) {
    return (
      <div
        data-testid="home-hero"
        aria-hidden
        className="mb-3 h-28 animate-pulse rounded-2xl bg-surface-3"
      />
    )
  }
  if (!data) {
    return (
      <Hero streakDays={streakDays} title="開始練習">
        <Primary to="/quick/swipe">開始練習</Primary>
      </Hero>
    )
  }

  const retake = data.retake
  if (retake?.gate.met) {
    return (
      <Hero
        streakDays={streakDays}
        title="可以再檢測了"
        note={`${fraudTypeLabel(retake.fraud_type)}已經練夠了。`}
      >
        <Primary to="/exam">去檢測</Primary>
      </Hero>
    )
  }
  if (retake) {
    return (
      <Hero
        streakDays={streakDays}
        title={`檢測沒過：先加強${fraudTypeLabel(retake.fraud_type)}`}
        note={gateRemaining(retake.gate)}
      >
        <Primary to="/quick/swipe">練滑卡</Primary>
        <Secondary to="/quick/quiz">練訊息判讀</Secondary>
        <Secondary to="/scenarios">練情境對抗</Secondary>
        <Link
          to="/exam"
          className="basis-full text-xs font-bold underline underline-offset-2"
        >
          查看重考資格
        </Link>
      </Hero>
    )
  }
  if (data.source === "none") {
    return (
      <Hero streakDays={streakDays} title="先做前測" note={data.note}>
        <Primary to="/pretest">做前測</Primary>
      </Hero>
    )
  }
  return (
    <Hero
      streakDays={streakDays}
      title={
        data.focus_label ? `本輪加強：${data.focus_label}` : "五類平均練習"
      }
      note={data.note}
    >
      {/* 三種訓練的入口就在正下方，這裡只放一個主按鈕 */}
      <Primary to="/quick/swipe">開始練習</Primary>
    </Hero>
  )
}

function Hero({
  title,
  note,
  streakDays,
  children,
}: {
  title: string
  note?: string
  streakDays: number
  children: ReactNode
}) {
  return (
    <section
      data-testid="home-hero"
      className="mb-3 overflow-hidden rounded-2xl bg-gradient-to-br from-primary to-accent p-4 text-primary-foreground shadow-lg"
    >
      <span className="mb-2 inline-flex items-center gap-1 rounded-full bg-primary-foreground/20 px-2 py-0.5 text-[10px] font-medium">
        <Target aria-hidden className="size-3" />
        下一步
      </span>
      <h2 className="font-bold">{title}</h2>
      {note && (
        <p className="mt-1 text-xs leading-relaxed opacity-90">{note}</p>
      )}
      <div className="mt-3 flex flex-wrap items-center gap-2">{children}</div>
      {streakDays > 0 && (
        <p className="mt-3 inline-flex items-center gap-1 text-[11px] opacity-90">
          <Flame aria-hidden className="size-3.5" />
          連續 {streakDays} 天 · 今天也別斷
        </p>
      )}
    </section>
  )
}

function Primary({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-1 rounded-xl bg-primary-foreground px-3 py-2 text-sm font-bold text-primary transition hover:brightness-95"
    >
      {children}
      <ChevronRight aria-hidden className="size-4" />
    </Link>
  )
}

function Secondary({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link
      to={to}
      className="rounded-xl bg-primary-foreground/20 px-3 py-2 text-sm font-bold transition hover:bg-primary-foreground/30"
    >
      {children}
    </Link>
  )
}
