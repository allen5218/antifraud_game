import { createFileRoute, Link } from "@tanstack/react-router"
import { CalendarCheck, Eye, Pencil, Trophy } from "lucide-react"
import { type FormEvent, useState } from "react"
import type {
  LeaderboardEntry,
  LeaderboardEntryPublic,
  LeaderboardResponse,
  SeasonBoardPublic,
  SeasonPublic,
} from "@/client"
import { PermanentBoards } from "@/components/progression/PermanentBoards"
import { PlayerShowcaseModal } from "@/components/progression/PlayerShowcaseModal"
import { extractErrorCode, useEconomyMe } from "@/hooks/useEconomy"
import {
  type LeaderboardPeriod,
  useLeaderboard,
  useUpdateNickname,
} from "@/hooks/useLeaderboard"
import {
  type BoardKind,
  useSeasonBoard,
  useSeasonCurrent,
} from "@/hooks/useSeasons"
import { formatDuration } from "@/lib/duration"
import { formatMoney } from "@/utils/money"

export const Route = createFileRoute("/_shell/leaderboard")({
  component: LeaderboardPage,
})

type ViewMode = "daily" | "season" | "permanent"

const DAILY_TABS: { period: LeaderboardPeriod; label: string }[] = [
  { period: "today", label: "今日" },
  { period: "week", label: "本週" },
]

const SEASON_BOARDS: { kind: BoardKind; label: string; desc: string }[] = [
  {
    kind: "accuracy",
    label: "正確率榜",
    desc: "依真實答對率排名，不計裝備倍率。同率先比有效題數，再比每題平均用時。",
  },
  {
    kind: "speed",
    label: "速度榜",
    desc: "正確率須達九成，再比較每題平均用時。用時包含閱讀、揭曉與網路等待。",
  },
  {
    kind: "power",
    label: "養成競技榜",
    desc: "每日答對比例換算積分，再乘上開局時的核心倍率與競技工具加成。",
  },
]

function LeaderboardPage() {
  const [viewMode, setViewMode] = useState<ViewMode>("daily")
  const [period, setPeriod] = useState<LeaderboardPeriod>("today")
  const [selectedBoard, setSelectedBoard] = useState<BoardKind>("accuracy")
  const [inspectPlayerId, setInspectPlayerId] = useState<string | null>(null)

  const { data: economy, isLoading: economyLoading } = useEconomyMe()
  const isDailyUnlocked = (economy?.level ?? 0) >= 5
  const trainingXp = economy?.xp ?? 0
  const xpGapToLv5 = Math.max(0, 1000 - trainingXp)

  // 每日排行（僅在達 Lv.5 解鎖後才發送請求，避免未解鎖時觸發 400 錯誤）
  const {
    data: dailyData,
    error: dailyError,
    isPending: dailyPending,
  } = useLeaderboard(period, Boolean(economy && isDailyUnlocked))

  // 當期賽季與三榜
  const { data: seasonData, isLoading: seasonLoading } = useSeasonCurrent()
  const { data: boardData, isLoading: boardLoading } = useSeasonBoard(
    seasonData?.id,
    selectedBoard,
  )

  return (
    <div className="flex flex-col gap-3 pb-8">
      <div>
        <h2 className="text-lg font-bold">競技排行榜</h2>
        <p className="text-xs text-muted-foreground">
          查看每日訓練成績與當期 14 天賽季榮譽。
        </p>
      </div>

      {/* 頂層分類：每日訓練 vs 14 天競技賽季 */}
      <div
        role="tablist"
        aria-label="排行榜類型"
        className="grid grid-cols-3 gap-1 rounded-xl bg-surface-2 p-1 text-xs font-bold"
      >
        <button
          type="button"
          role="tab"
          aria-selected={viewMode === "daily"}
          onClick={() => setViewMode("daily")}
          className={
            viewMode === "daily"
              ? "rounded-lg bg-surface-3 py-1.5 shadow-xs text-foreground"
              : "rounded-lg py-1.5 text-muted-foreground"
          }
        >
          每日訓練榜
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={viewMode === "season"}
          onClick={() => setViewMode("season")}
          className={
            viewMode === "season"
              ? "rounded-lg bg-surface-3 py-1.5 shadow-xs text-foreground"
              : "rounded-lg py-1.5 text-muted-foreground"
          }
        >
          14天競技賽季
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={viewMode === "permanent"}
          onClick={() => setViewMode("permanent")}
          className={
            viewMode === "permanent"
              ? "rounded-lg bg-surface-3 py-1.5 text-foreground"
              : "py-1.5 text-muted-foreground"
          }
        >
          永久養成榜
        </button>
      </div>

      {/* 每日訓練排行榜 */}
      {viewMode === "daily" &&
        !economyLoading &&
        (!isDailyUnlocked ||
          extractErrorCode(dailyError) === "level_required") && (
          <div className="flex flex-col items-center gap-2.5 rounded-xl border border-border bg-card p-5 text-center">
            <p className="text-xs font-bold text-foreground">
              每日訓練在訓練等級 Lv.5 解鎖（目前 Lv.{economy?.level ?? 1}，還差{" "}
              {xpGapToLv5} 訓練 XP）
            </p>
            <p className="text-xs text-muted-foreground">
              你也可以先查看「14天競技賽季」與「永久養成榜」，或前往訊息判讀累積訓練經驗。
            </p>
            <div className="mt-1 flex flex-wrap justify-center gap-2">
              <Link
                to="/quick/quiz"
                className="rounded-lg bg-primary px-3 py-1.5 text-xs font-bold text-primary-foreground"
              >
                去訊息判讀升等
              </Link>
              <button
                type="button"
                onClick={() => setViewMode("permanent")}
                className="rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-xs font-semibold text-foreground"
              >
                看永久養成榜
              </button>
            </div>
          </div>
        )}
      {viewMode === "daily" &&
        dailyError &&
        extractErrorCode(dailyError) !== "level_required" && (
          <p className="py-6 text-center text-xs text-muted-foreground">
            每日排行載入失敗，請稍後重試。
          </p>
        )}
      {viewMode === "daily" && isDailyUnlocked && !dailyError && (
        <DailyLeaderboardView
          period={period}
          onPeriodChange={setPeriod}
          data={dailyData}
          isPending={dailyPending}
        />
      )}
      {viewMode === "permanent" && (
        <PermanentBoards onInspect={setInspectPlayerId} />
      )}

      {/* 14 天賽季三大排行榜 */}
      {viewMode === "season" && (
        <SeasonLeaderboardView
          season={seasonData}
          seasonLoading={seasonLoading}
          boardKind={selectedBoard}
          onBoardChange={setSelectedBoard}
          boardData={boardData}
          boardLoading={boardLoading}
          onInspectPlayer={setInspectPlayerId}
          isDailyUnlocked={isDailyUnlocked}
          xpGapToLv5={xpGapToLv5}
        />
      )}

      {/* 公開名片 Modal */}
      <PlayerShowcaseModal
        playerId={inspectPlayerId}
        onClose={() => setInspectPlayerId(null)}
      />
    </div>
  )
}

function DailyLeaderboardView({
  period,
  onPeriodChange,
  data,
  isPending,
}: {
  period: LeaderboardPeriod
  onPeriodChange: (p: LeaderboardPeriod) => void
  data: LeaderboardResponse | undefined
  isPending: boolean
}) {
  const meOutside = data?.me && !data.entries.some((entry) => entry.is_me)

  return (
    <div className="flex flex-col gap-3">
      <div
        role="tablist"
        aria-label="排行期間"
        className="grid grid-cols-2 gap-1 rounded-xl bg-surface-2 p-1"
      >
        {DAILY_TABS.map((tab) => (
          <button
            key={tab.period}
            type="button"
            role="tab"
            aria-selected={period === tab.period}
            onClick={() => onPeriodChange(tab.period)}
            className={
              period === tab.period
                ? "rounded-lg bg-surface-3 py-1 text-xs font-bold shadow-xs text-foreground"
                : "rounded-lg py-1 text-xs text-muted-foreground"
            }
          >
            {tab.label}
          </button>
        ))}
      </div>

      {isPending || !data ? (
        <p className="py-8 text-center text-xs text-muted-foreground">
          載入中…
        </p>
      ) : data.entries.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-xl border border-border bg-surface-3 p-6 text-center">
          <p className="text-sm">
            {period === "today"
              ? "今天還沒有人完成每日訓練"
              : "這 7 天還沒有人完成每日訓練"}
          </p>
          <Link
            to="/daily"
            className="inline-flex items-center gap-1 text-sm font-bold text-primary"
          >
            <CalendarCheck aria-hidden className="size-4" />
            去做每日訓練
          </Link>
        </div>
      ) : (
        <ol className="m-0 flex list-none flex-col gap-1.5 p-0">
          {data.entries.map((entry: LeaderboardEntry) => (
            <DailyRow key={entry.rank} entry={entry} period={period} />
          ))}
          {meOutside && data.me && (
            <>
              <li aria-hidden className="text-center text-muted-foreground">
                ⋮
              </li>
              <DailyRow entry={data.me} period={period} />
            </>
          )}
        </ol>
      )}

      {data && !data.me && data.entries.length > 0 && (
        <Link
          to="/daily"
          className="text-center text-xs font-bold text-primary underline"
        >
          {period === "today"
            ? "你今天還沒做每日訓練，完成後就會上榜"
            : "完成每日訓練就會上榜"}
        </Link>
      )}

      {data && <NicknameForm current={data.nickname ?? null} />}
    </div>
  )
}

function DailyRow({
  entry,
  period,
}: {
  entry: LeaderboardEntry
  period: LeaderboardPeriod
}) {
  return (
    <li
      data-testid={entry.is_me ? "leaderboard-me" : undefined}
      className={`flex items-center gap-3 rounded-xl border px-3 py-2 ${
        entry.is_me
          ? "border-primary bg-primary/10"
          : "border-border bg-surface-3"
      }`}
    >
      <span
        className={`w-7 shrink-0 text-center text-sm font-extrabold ${
          entry.rank <= 3 ? "text-warning" : "text-muted-foreground"
        }`}
      >
        {entry.rank}
      </span>
      <span className="min-w-0 flex-1 truncate text-sm font-semibold">
        {entry.name}
        {entry.is_me && (
          <span className="ml-1.5 rounded bg-primary px-1 py-0.5 text-[10px] text-primary-foreground">
            你
          </span>
        )}
      </span>
      <span className="shrink-0 text-right">
        <span className="block text-sm font-bold">
          {period === "today"
            ? `${entry.correct} / ${entry.total}`
            : `答對 ${entry.correct}`}
        </span>
        <span className="block text-[10px] text-muted-foreground">
          {period === "today"
            ? formatDuration(entry.duration_seconds)
            : `練了 ${entry.days} 天`}
        </span>
      </span>
    </li>
  )
}

function SeasonLeaderboardView({
  season,
  seasonLoading,
  boardKind,
  onBoardChange,
  boardData,
  boardLoading,
  onInspectPlayer,
  isDailyUnlocked,
  xpGapToLv5,
}: {
  season: SeasonPublic | undefined
  seasonLoading: boolean
  boardKind: BoardKind
  onBoardChange: (k: BoardKind) => void
  boardData: SeasonBoardPublic | undefined
  boardLoading: boolean
  onInspectPlayer: (id: string) => void
  isDailyUnlocked: boolean
  xpGapToLv5: number
}) {
  if (seasonLoading || !season) {
    return (
      <div className="py-8 text-center text-xs text-muted-foreground">
        載入賽季中…
      </div>
    )
  }

  const qualifiedDays = season.my_qualified_days ?? 0
  const myEntry = boardData?.my_entry
  const isQualified = Boolean(myEntry?.is_qualified)
  const activeBoardMeta = SEASON_BOARDS.find((b) => b.kind === boardKind)!

  return (
    <div className="flex flex-col gap-3">
      {/* 賽季狀態卡 */}
      <div className="rounded-xl border border-border bg-card p-3.5 text-card-foreground">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 font-bold">
            <Trophy className="size-4 text-warning" />
            <span>{season.name}</span>
          </div>
          <span className="rounded-full bg-surface-2 px-2 py-0.5 text-[10px] text-muted-foreground">
            剩餘 {season.days_remaining} 天
          </span>
        </div>

        {/* 資格進度條 */}
        <div className="mt-2.5 rounded-lg bg-surface-2 p-2.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-muted-foreground">
              參賽進度：{qualifiedDays}／5 天 · {season.my_total_questions ?? 0}
              ／50 題
            </span>
            <span
              className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                isQualified
                  ? "bg-legit/20 text-legit"
                  : "bg-warning/20 text-warning"
              }`}
            >
              {isQualified
                ? "已具備結算資格"
                : myEntry
                  ? "暫列（未滿資格）"
                  : "未入榜"}
            </span>
          </div>
          <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-muted">
            <div
              className={`h-full transition-all ${isQualified ? "bg-legit" : "bg-warning"}`}
              style={{ width: `${Math.min(100, (qualifiedDays / 5) * 100)}%` }}
            />
          </div>
          <p className="mt-1.5 text-[10px] text-muted-foreground">
            {isQualified
              ? "恭喜！賽季結束後將按最終正式排名派發專屬突破素材與高階榮譽。"
              : "每期須完成至少 5 天、50 題每日訓練方可列入正式結算發獎。速度榜另須達到九成正確率。"}
          </p>
          {!isQualified && (
            <div className="mt-2 flex items-center justify-between border-t border-border/50 pt-2 text-[11px]">
              <span className="text-muted-foreground">
                {isDailyUnlocked
                  ? `還差 ${Math.max(0, 5 - qualifiedDays)} 天每日訓練達標`
                  : `每日訓練於 Lv.5 解鎖（還差 ${xpGapToLv5} 訓練 XP）`}
              </span>
              <Link
                to={isDailyUnlocked ? "/daily" : "/quick/quiz"}
                className="font-bold text-primary underline"
              >
                {isDailyUnlocked ? "去做今日訓練" : "去訊息判讀升等"}
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* 三榜切換 */}
      <div
        role="tablist"
        aria-label="賽季排行榜切換"
        className="grid grid-cols-3 gap-1 rounded-xl bg-surface-2 p-1"
      >
        {SEASON_BOARDS.map((b) => (
          <button
            key={b.kind}
            type="button"
            role="tab"
            aria-selected={boardKind === b.kind}
            onClick={() => onBoardChange(b.kind)}
            className={
              boardKind === b.kind
                ? "rounded-lg bg-surface-3 py-1 text-xs font-bold shadow-xs text-foreground"
                : "rounded-lg py-1 text-xs text-muted-foreground"
            }
          >
            {b.label}
          </button>
        ))}
      </div>

      {/* 榜別說明 */}
      <div className="rounded-lg bg-muted/40 px-3 py-2 text-[11px] text-muted-foreground">
        {activeBoardMeta.desc}
      </div>

      {/* 榜單清單 */}
      {boardLoading || !boardData ? (
        <div className="py-8 text-center text-xs text-muted-foreground">
          載入榜單中…
        </div>
      ) : boardData.entries.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-xl border border-border bg-surface-3 p-6 text-center text-xs text-muted-foreground">
          <p>本期賽季此榜單尚無參賽紀錄，完成今日訓練即可率先上榜！</p>
          <Link
            to={isDailyUnlocked ? "/daily" : "/quick/quiz"}
            className="mt-1 rounded-lg bg-primary px-3 py-1.5 text-xs font-bold text-primary-foreground"
          >
            {isDailyUnlocked ? "前往每日訓練" : "去訊息判讀升至 Lv.5"}
          </Link>
        </div>
      ) : (
        <ol className="m-0 flex list-none flex-col gap-1.5 p-0">
          {boardData.entries.map((entry: LeaderboardEntryPublic) => (
            <SeasonRow
              key={entry.user_id}
              entry={entry}
              boardKind={boardKind}
              onInspect={() => onInspectPlayer(entry.user_id)}
            />
          ))}
          {/* 我的排名釘選 */}
          {myEntry && !boardData.entries.some((e) => e.is_me) && (
            <>
              <li aria-hidden className="text-center text-muted-foreground">
                ⋮
              </li>
              <SeasonRow
                entry={myEntry}
                boardKind={boardKind}
                onInspect={() => onInspectPlayer(myEntry.user_id)}
              />
            </>
          )}
        </ol>
      )}
    </div>
  )
}

function SeasonRow({
  entry,
  boardKind,
  onInspect,
}: {
  entry: LeaderboardEntryPublic
  boardKind: BoardKind
  onInspect: () => void
}) {
  const metrics = entry.metrics ?? {}

  const renderMetric = () => {
    if (boardKind === "accuracy") {
      const acc = Number(metrics.accuracy ?? 0)
      const correct = String(metrics.correct ?? 0)
      const total = String(metrics.total ?? 0)
      return (
        <div className="text-right">
          <div className="text-sm font-extrabold text-legit">
            {(acc * 100).toFixed(1)}%
          </div>
          <div className="text-[10px] text-muted-foreground">
            答對 {correct} / {total}
          </div>
        </div>
      )
    }
    if (boardKind === "speed") {
      const avg = Number(metrics.avg_seconds_per_question ?? 0)
      return (
        <div className="text-right">
          <div className="text-sm font-extrabold text-primary">{avg} 秒/題</div>
          <div className="text-[10px] text-muted-foreground">
            有效作答 {String(metrics.total ?? 0)} 題
          </div>
        </div>
      )
    }
    // power
    const pts = String(metrics.power_points ?? "0")
    return (
      <div className="text-right">
        <div className="text-sm font-extrabold text-warning">
          {formatMoney(pts)} 分
        </div>
        <div className="text-[10px] text-muted-foreground">綜合競技分</div>
      </div>
    )
  }

  return (
    <li
      className={`flex items-center gap-2.5 rounded-xl border px-3 py-2 text-xs ${
        entry.is_me
          ? "border-primary bg-primary/10"
          : "border-border bg-surface-3"
      }`}
    >
      <span
        className={`w-8 shrink-0 text-center text-sm font-black ${
          entry.is_qualified && entry.rank <= 3
            ? "text-warning"
            : "text-muted-foreground"
        }`}
      >
        {entry.is_qualified ? entry.rank : `暫${entry.rank}`}
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5 font-bold">
          <span className="truncate">{entry.nickname}</span>
          {entry.is_me && (
            <span className="rounded bg-primary px-1 py-0.2 text-[9px] text-primary-foreground">
              你
            </span>
          )}
          <span
            className={`rounded px-1 py-0.2 text-[9px] font-semibold ${
              entry.is_qualified
                ? "bg-legit/20 text-legit"
                : "bg-warning/20 text-warning"
            }`}
          >
            {entry.is_qualified ? "正式" : "暫列"}
          </span>
        </div>
      </div>
      <div className="shrink-0">{renderMetric()}</div>
      <button
        type="button"
        onClick={onInspect}
        title="查看公開名片"
        className="rounded-lg p-1 text-muted-foreground hover:bg-muted"
      >
        <Eye className="size-3.5" />
      </button>
    </li>
  )
}

const NICKNAME_ERRORS: Record<string, string> = {
  too_long: "暱稱最多 12 個字",
  contact_info: "暱稱不能放聯絡方式（email、網址、LINE、電話）",
}

function NicknameForm({ current }: { current: string | null }) {
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState(current ?? "")
  const update = useUpdateNickname()

  const errorText = (() => {
    if (!update.error) return null
    const body = (update.error as { body?: { detail?: { reason?: string } } })
      .body
    return (
      NICKNAME_ERRORS[body?.detail?.reason ?? ""] ?? "暱稱儲存失敗，請再試一次"
    )
  })()

  const submit = (event: FormEvent) => {
    event.preventDefault()
    update.mutate(value, { onSuccess: () => setEditing(false) })
  }

  if (!editing) {
    return (
      <div className="flex items-center justify-between gap-2 rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs">
        <span className="text-muted-foreground">
          排行榜上的名字：
          <span className="font-semibold text-foreground">
            {current ?? "尚未設定（顯示匿名）"}
          </span>
        </span>
        <button
          type="button"
          onClick={() => {
            setValue(current ?? "")
            update.reset()
            setEditing(true)
          }}
          className="inline-flex shrink-0 items-center gap-1 font-bold text-primary"
        >
          <Pencil aria-hidden className="size-3.5" />
          {current ? "修改" : "設定暱稱"}
        </button>
      </div>
    )
  }

  return (
    <form
      onSubmit={submit}
      className="flex flex-col gap-2 rounded-xl border border-border bg-surface-2 p-3 text-xs"
    >
      <label htmlFor="nickname" className="font-semibold">
        排行榜暱稱（最多 12 字，留空就顯示匿名）
      </label>
      <input
        id="nickname"
        value={value}
        maxLength={12}
        onChange={(event) => setValue(event.target.value)}
        className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
      />
      {errorText && <p className="text-destructive">{errorText}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={update.isPending}
          className="flex-1 rounded-lg bg-primary py-2 font-bold text-primary-foreground"
        >
          儲存
        </button>
        <button
          type="button"
          onClick={() => setEditing(false)}
          className="flex-1 rounded-lg border border-border py-2"
        >
          取消
        </button>
      </div>
    </form>
  )
}
