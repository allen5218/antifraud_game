import { Link } from "@tanstack/react-router"
import { CircleHelp, House, Sparkles, Trophy, Wallet } from "lucide-react"
import { useEffect, useState } from "react"
import type { EstatePublic } from "@/client"
import { guideSeen, markGuideSeen } from "@/components/progression/guideSteps"
import { Honors } from "@/components/progression/Honors"
import { ProgressionGuide } from "@/components/progression/ProgressionGuide"
import useCustomToast from "@/hooks/useCustomToast"
import { extractErrorCode } from "@/hooks/useEconomy"
import {
  useAssignManager,
  useBuyCard,
  useBuyIndustry,
  useCollectRent,
  useEstate,
  useLegacySeen,
  useMoveHouse,
} from "@/hooks/useEstate"
import { useHomeSummary } from "@/hooks/useHomeSummary"
import { parseBigIntSafe } from "@/utils/money"
import {
  AwayDialog,
  IndustryDetailDialog,
  LegacyDialog,
  ManagerDialog,
  MoveDialog,
} from "./EstateDialogs"
import { projectCash } from "./estateClock"
import { formatYuan, perSecond } from "./format"
import { IndustryRow } from "./IndustryRow"

const ERRORS: Record<string, string> = {
  insufficient_cash: "錢不夠",
  revision_mismatch: "畫面舊了，已經幫你重新整理",
  no_reputation: "再多收一點租才換得到信譽",
  mascot_not_owned: "還沒有這隻吉祥物",
  industry_not_owned: "還沒有這種房產",
  card_maxed: "升級卡已經滿了",
}

/** 重讀之後過了幾秒；每 0.25 秒更新，讓進度條與錢跑起來 */
function useElapsed(since: number): number {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 250)
    return () => window.clearInterval(id)
  }, [])
  return Math.max(0, (now - since) / 1000)
}

/**
 * 分頁「經營」：像 AdVenture Capitalist 的放置經營。
 * 最上面是總資產與每秒收入，下面一列列房產各自收租，最下面是搬家換信譽與榮譽。
 */
export function EstatePage() {
  const { data, dataUpdatedAt, isError, refetch } = useEstate()
  const { data: home } = useHomeSummary()
  const elapsed = useElapsed(dataUpdatedAt)
  const { showErrorToast } = useCustomToast()
  const buy = useBuyIndustry()
  const collect = useCollectRent()
  const card = useBuyCard()
  const manager = useAssignManager()
  const move = useMoveHouse()
  const legacySeen = useLegacySeen()
  const [detailTier, setDetailTier] = useState<number | null>(null)
  const [managerTier, setManagerTier] = useState<number | null>(null)
  const [moveOpen, setMoveOpen] = useState(false)
  const [awayKey, setAwayKey] = useState<string | null>(null)
  const [guideOpen, setGuideOpen] = useState(() => !guideSeen())

  const busy =
    buy.isPending ||
    collect.isPending ||
    card.isPending ||
    manager.isPending ||
    move.isPending

  const onError = (err: unknown) => {
    const code = extractErrorCode(err)
    showErrorToast((code && ERRORS[code]) || "請稍後再試一次")
    refetch()
  }

  if (isError) {
    return (
      <p role="alert" className="mx-auto max-w-md p-4 text-sm text-scam">
        經營載入失敗，請重新整理。
      </p>
    )
  }
  if (!data) {
    return (
      <div className="mx-auto max-w-md space-y-3">
        <div className="h-36 animate-pulse rounded-3xl bg-surface-2" />
        <div className="h-24 animate-pulse rounded-2xl bg-surface-2" />
        <div className="h-24 animate-pulse rounded-2xl bg-surface-2" />
      </div>
    )
  }
  if (data.elder_mode) return <ElderEstate estate={data} />

  const cash = projectCash(data, elapsed)
  const extra = cash - parseBigIntSafe(data.cash)
  const total = parseBigIntSafe(data.total_assets) + extra
  const detail = data.industries.find((i) => i.tier_id === detailTier) ?? null
  const managing =
    data.industries.find((i) => i.tier_id === managerTier) ?? null
  const stage = Math.max(
    1,
    ...data.industries.filter((i) => i.owned > 0).map((i) => i.tier_id),
  )
  const away = data.away && awayKey !== data.server_time ? data.away : null
  const mascot = home?.mascot_image_url ?? "/assets/mascot/shiba/base.webp"

  return (
    <div data-testid="estate-page" className="mx-auto max-w-md space-y-4">
      <section
        aria-label="總資產"
        className="rounded-3xl border border-border bg-card p-5 shadow-sm"
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm text-muted-foreground">總資產</p>
            <p
              data-testid="estate-total"
              className="mt-1 text-3xl font-extrabold tabular-nums"
            >
              {formatYuan(total)}
              <span className="ml-1 text-lg font-bold text-muted-foreground">
                元
              </span>
            </p>
            <p className="mt-1 text-sm font-semibold text-legit tabular-nums">
              每秒 {perSecond(data.income_per_hour)} 元
            </p>
          </div>
          <button
            type="button"
            onClick={() => setGuideOpen(true)}
            className="flex items-center gap-1 rounded-xl bg-surface-2 px-3 py-2 text-sm font-bold"
          >
            <CircleHelp aria-hidden className="size-4" />
            怎麼玩
          </button>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-3">
          <Stat
            icon={<Wallet aria-hidden className="size-5 text-primary" />}
            label="手上的錢"
            value={`${formatYuan(cash)} 元`}
            testId="estate-cash"
          />
          <Stat
            icon={<Sparkles aria-hidden className="size-5 text-warning" />}
            label="信譽"
            value={`${formatYuan(data.reputation)} 點`}
          />
        </div>
      </section>

      <Link
        to="/room"
        search={{ view: "house" }}
        data-testid="estate-house"
        className="flex items-center gap-3 overflow-hidden rounded-2xl border border-border bg-card p-2 pr-4 hover:bg-surface-2"
      >
        <img
          src={`/assets/room/${stage}/bg.webp`}
          alt=""
          className="h-20 w-16 shrink-0 rounded-xl object-cover object-top"
        />
        <div className="min-w-0 flex-1">
          <p className="flex items-center gap-1 font-bold">
            <House aria-hidden className="size-4 text-primary" />
            我的家
          </p>
          <p className="text-sm text-muted-foreground">
            住在最好的房產裡，進去看看
          </p>
        </div>
      </Link>

      <section aria-label="房產" className="space-y-2">
        <h2 className="px-1 text-base font-bold">房產</h2>
        <ul className="space-y-2">
          {data.industries.map((industry) => (
            <IndustryRow
              key={industry.tier_id}
              industry={industry}
              elapsed={elapsed}
              cash={cash}
              busy={busy}
              onBuy={() =>
                buy.mutate(
                  {
                    tierId: industry.tier_id,
                    expectedOwned: industry.owned,
                  },
                  { onError },
                )
              }
              onCollect={() => collect.mutate(industry.tier_id, { onError })}
              onDetail={() => setDetailTier(industry.tier_id)}
              onManager={() => setManagerTier(industry.tier_id)}
            />
          ))}
        </ul>
      </section>

      <MoveCard estate={data} onOpen={() => setMoveOpen(true)} />

      <Honors />
      <Link
        to="/leaderboard"
        className="flex items-center justify-center gap-1 text-sm text-muted-foreground underline"
      >
        <Trophy aria-hidden className="size-4" />
        看兩週競技榜與永久榜
      </Link>

      <IndustryDetailDialog
        industry={detail}
        reputation={formatYuan(data.reputation)}
        reputationPercent={formatYuan(data.reputation_percent)}
        cash={cash}
        busy={busy}
        onClose={() => setDetailTier(null)}
        onBuyCard={() =>
          detail &&
          card.mutate(
            { tierId: detail.tier_id, expectedLevel: detail.card_level },
            { onError },
          )
        }
      />
      <ManagerDialog
        industry={managing}
        estate={data}
        busy={busy}
        onClose={() => setManagerTier(null)}
        onPick={(itemId) =>
          managing &&
          manager.mutate(
            { tierId: managing.tier_id, itemId },
            { onError, onSuccess: () => setManagerTier(null) },
          )
        }
      />
      <MoveDialog
        estate={data}
        open={moveOpen}
        busy={busy}
        onClose={() => setMoveOpen(false)}
        onConfirm={() =>
          move.mutate(data.moves, {
            onError,
            onSuccess: () => setMoveOpen(false),
          })
        }
      />
      {!guideOpen && (
        <LegacyDialog
          lines={data.legacy_lines}
          busy={legacySeen.isPending}
          onClose={() => legacySeen.mutate(undefined)}
        />
      )}
      {!guideOpen && data.legacy_lines.length === 0 && (
        <AwayDialog away={away} onClose={() => setAwayKey(data.server_time)} />
      )}
      <ProgressionGuide
        open={guideOpen}
        mascotSrc={mascot}
        onClose={() => {
          markGuideSeen()
          setGuideOpen(false)
        }}
      />
    </div>
  )
}

function Stat({
  icon,
  label,
  value,
  testId,
}: {
  icon: React.ReactNode
  label: string
  value: string
  testId?: string
}) {
  return (
    <div className="flex items-center gap-2 rounded-2xl bg-surface-2 px-3 py-2">
      {icon}
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p data-testid={testId} className="truncate font-bold tabular-nums">
          {value}
        </p>
      </div>
    </div>
  )
}

function MoveCard({
  estate,
  onOpen,
}: {
  estate: EstatePublic
  onOpen: () => void
}) {
  const gain = parseBigIntSafe(estate.pending_reputation)
  const need =
    parseBigIntSafe(estate.next_reputation_at) -
    parseBigIntSafe(estate.lifetime_earnings)
  return (
    <section
      aria-label="搬家換信譽"
      className="rounded-3xl border border-border bg-card p-4"
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="font-bold">搬家換信譽</h2>
          <p className="text-sm text-muted-foreground">
            現在收入是原本的 {formatYuan(estate.reputation_percent)}%
          </p>
        </div>
        <button
          type="button"
          onClick={onOpen}
          disabled={gain <= 0n}
          data-testid="move-open"
          className="shrink-0 rounded-xl bg-primary px-4 py-2 font-bold text-primary-foreground disabled:bg-surface-2 disabled:text-muted-foreground"
        >
          搬家
        </button>
      </div>
      <p className="mt-2 text-sm">
        {gain > 0n
          ? `現在搬家可以拿 ${formatYuan(gain)} 點信譽`
          : `再收 ${formatYuan(need > 0n ? need : 0n)} 元租金，搬家就能拿到信譽`}
      </p>
    </section>
  )
}

/** 年長者模式：沒有經營，只有一間自己的房子和存款 */
function ElderEstate({ estate }: { estate: EstatePublic }) {
  const elder = estate.elder
  if (!elder) return null
  return (
    <div className="mx-auto max-w-md space-y-3">
      <section className="rounded-3xl border border-border bg-card p-5">
        <p className="text-sm text-muted-foreground">{elder.home_name}</p>
        <p className="mt-1 text-2xl font-extrabold">
          {formatYuan(elder.home_value)} 元
        </p>
      </section>
      <section className="rounded-3xl border border-border bg-card p-5">
        <p className="text-sm text-muted-foreground">存款</p>
        <p className="mt-1 text-2xl font-extrabold">
          {formatYuan(elder.savings)} 元
        </p>
      </section>
    </div>
  )
}
