import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { EstateService } from "@/client"
import { formatYuan } from "@/components/estate/format"

export function PermanentBoards({
  onInspect,
}: {
  onInspect: (id: string) => void
}) {
  const [kind, setKind] = useState<"wealth" | "reputation">("wealth")
  const { data, isError, isPending } = useQuery({
    queryKey: ["estate-board", kind],
    queryFn: () => EstateService.estateBoard({ kind }),
    staleTime: 15_000,
  })
  return (
    <section className="flex flex-col gap-3" aria-label="永久經營排行榜">
      <div
        className="grid grid-cols-2 gap-1 rounded-xl bg-surface-2 p-1"
        role="tablist"
        aria-label="長期排行項目"
      >
        {(
          [
            ["wealth", "歷來租金"],
            ["reputation", "信譽"],
          ] as const
        ).map(([value, label]) => (
          <button
            key={value}
            type="button"
            role="tab"
            aria-selected={kind === value}
            onClick={() => setKind(value)}
            className={
              kind === value
                ? "rounded-lg bg-card p-2 text-xs font-bold"
                : "p-2 text-xs text-muted-foreground"
            }
          >
            {label}
          </button>
        ))}
      </div>
      <p className="text-xs text-muted-foreground">
        {kind === "wealth"
          ? "經營以來收到的租金加總，花錢和搬家都不會變少。"
          : "搬家和賽季拿到的信譽。"}
      </p>
      {isPending && <p className="p-6 text-center text-xs">載入排行…</p>}
      {isError && (
        <p role="alert" className="text-sm text-scam">
          排行載入失敗，請稍後重試。
        </p>
      )}
      {data?.my_entry && (
        <p className="rounded-xl bg-primary/10 p-3 text-sm font-bold text-primary">
          我的位置：第 {data.my_entry.rank} 名 ·{" "}
          {formatYuan(data.my_entry.score)}
          {kind === "wealth" ? " 元" : " 點"}
        </p>
      )}
      {data && !data.entries.length && (
        <p className="py-6 text-center text-xs text-muted-foreground">
          去經營收租，開始累積。
        </p>
      )}
      <ol className="flex flex-col gap-2">
        {data?.entries.map((entry) => (
          <li key={entry.user_id}>
            <button
              type="button"
              onClick={() => onInspect(entry.user_id)}
              className="flex w-full items-center justify-between rounded-xl border border-border bg-card p-3 text-left text-sm"
            >
              <span>
                <strong className="mr-3">{entry.rank}</strong>
                {entry.nickname}
              </span>
              <span className="font-bold text-primary">
                {formatYuan(entry.score)}
              </span>
            </button>
          </li>
        ))}
      </ol>
    </section>
  )
}
