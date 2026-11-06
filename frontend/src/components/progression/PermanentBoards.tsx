import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { CollectionsService } from "@/client"
import { formatMoney } from "@/utils/money"

export function PermanentBoards({
  onInspect,
}: {
  onInspect: (id: string) => void
}) {
  const [kind, setKind] = useState<"wealth" | "houses" | "pets">("wealth")
  const { data, isError, isPending } = useQuery({
    queryKey: ["collection-board", kind],
    queryFn: () => CollectionsService.permanentBoard({ kind }),
    staleTime: 15_000,
  })
  return (
    <section className="flex flex-col gap-3" aria-label="永久養成排行榜">
      <div
        className="grid grid-cols-3 gap-1 rounded-xl bg-surface-2 p-1"
        role="tablist"
        aria-label="長期排行項目"
      >
        {(
          [
            ["wealth", "累積所得"],
            ["houses", "房屋建設"],
            ["pets", "寵物收藏"],
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
          ? "自養成版本啟用起累積的訓練收入，消費不扣分，退款與變賣不加分。"
          : "每種收藏基礎 100 分，加上養成等級平方乘以 10。房屋只計目前持有的種類，重複購買不重複算。"}
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
          {formatMoney(data.my_entry.score, { abbreviated: true })} 分
        </p>
      )}
      {data && !data.entries.length && (
        <p className="py-6 text-center text-xs text-muted-foreground">
          完成一輪訓練，開始累積你的長期地位。
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
                {formatMoney(entry.score, { abbreviated: true })}
              </span>
            </button>
          </li>
        ))}
      </ol>
    </section>
  )
}
