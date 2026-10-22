import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import {
  type Filters,
  TABS,
  TeamBankList,
  TeamFilters,
  type TeamTab,
} from "@/components/team/TeamBank"
import { extractErrorCode } from "@/hooks/useEconomy"
import { teamBankQuery, useTeamBank } from "@/hooks/useTeam"
import { warmQueries } from "@/lib/prefetch"

export const Route = createFileRoute("/_shell/team")({
  loader: ({ context: { queryClient } }) => {
    warmQueries(queryClient, [teamBankQuery])
  },
  component: TeamPage,
})

function TeamPage() {
  const [tab, setTab] = useState<TeamTab>("pretest")
  const [filters, setFilters] = useState<Filters>({
    type: "all",
    truth: "all",
    query: "",
  })
  const { data, error, isPending } = useTeamBank()

  if (error) {
    return (
      <p className="py-12 text-center text-xs text-muted-foreground">
        {extractErrorCode(error) === "team_required"
          ? "團隊題庫只開放給團隊成員。"
          : "團隊題庫載入失敗，請稍後再試"}
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <div>
        <h2 className="text-lg font-bold">團隊題庫</h2>
        <p className="text-xs text-muted-foreground">
          全部題目與答案，只有團隊看得到。
        </p>
      </div>
      <div
        role="tablist"
        aria-label="玩法"
        className="grid grid-cols-5 gap-1 rounded-xl bg-surface-2 p-1"
      >
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={
              tab === t.id
                ? "rounded-lg bg-surface-3 py-1.5 text-xs font-bold shadow-sm"
                : "rounded-lg py-1.5 text-xs text-muted-foreground"
            }
          >
            {t.label}
          </button>
        ))}
      </div>
      <TeamFilters filters={filters} onChange={setFilters} />
      {isPending || !data ? (
        <p className="py-8 text-center text-xs text-muted-foreground">
          載入中…
        </p>
      ) : (
        <TeamBankList bank={data} tab={tab} filters={filters} />
      )}
    </div>
  )
}
