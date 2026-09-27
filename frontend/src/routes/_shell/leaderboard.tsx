import { createFileRoute, Link } from "@tanstack/react-router"
import { CalendarCheck, Pencil } from "lucide-react"
import { type FormEvent, useState } from "react"
import type { LeaderboardEntry } from "@/client"
import { extractErrorCode } from "@/hooks/useEconomy"
import {
  type LeaderboardPeriod,
  useLeaderboard,
  useUpdateNickname,
} from "@/hooks/useLeaderboard"
import { formatDuration } from "@/lib/duration"

export const Route = createFileRoute("/_shell/leaderboard")({
  component: LeaderboardPage,
})

const TABS: { period: LeaderboardPeriod; label: string }[] = [
  { period: "today", label: "今日" },
  { period: "week", label: "本週" },
]

function LeaderboardPage() {
  const [period, setPeriod] = useState<LeaderboardPeriod>("today")
  const { data, error, isPending } = useLeaderboard(period)

  if (error) {
    return (
      <p className="py-12 text-center text-xs text-muted-foreground">
        {extractErrorCode(error) === "level_required"
          ? "排行榜在 Lv.5 解鎖，先到題組或滑卡多練幾輪。"
          : "排行榜載入失敗，請稍後再試"}
      </p>
    )
  }

  const meOutside = data?.me && !data.entries.some((entry) => entry.is_me)

  return (
    <div className="flex flex-col gap-3">
      <div>
        <h2 className="text-lg font-bold">排行榜</h2>
        <p className="text-xs text-muted-foreground">
          依每日訓練的成績排名，答對一樣多時比速度。
        </p>
      </div>

      <div
        role="tablist"
        aria-label="排行期間"
        className="grid grid-cols-2 gap-1 rounded-xl bg-surface-2 p-1"
      >
        {TABS.map((tab) => (
          <button
            key={tab.period}
            type="button"
            role="tab"
            aria-selected={period === tab.period}
            onClick={() => setPeriod(tab.period)}
            className={
              period === tab.period
                ? "rounded-lg bg-surface-3 py-1.5 text-sm font-bold shadow-sm"
                : "rounded-lg py-1.5 text-sm text-muted-foreground"
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
          {data.entries.map((entry) => (
            <Row key={entry.rank} entry={entry} period={period} />
          ))}
          {meOutside && data.me && (
            <>
              <li aria-hidden className="text-center text-muted-foreground">
                ⋮
              </li>
              <Row entry={data.me} period={period} />
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

function Row({
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
