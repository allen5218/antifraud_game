import { useQuery } from "@tanstack/react-query"
import { Award } from "lucide-react"
import { BadgesService } from "@/client/sdk.gen"
import { Button } from "@/components/ui/button"

export function PublicBadge({ slug }: { slug: string }) {
  const query = useQuery({
    queryKey: ["public-badge", slug],
    queryFn: () => BadgesService.publicBadge({ slug }),
    retry: false,
  })
  const badge = query.data
  return (
    <main className="mx-auto flex min-h-dvh max-w-md items-center p-4">
      <section className="w-full space-y-4 rounded-2xl border bg-card p-6">
        <h1 className="flex items-center gap-2 text-xl font-bold">
          <Award aria-hidden className="size-6 text-warning" />
          徽章查驗
        </h1>
        {query.isError ? (
          <>
            <p role="alert">
              {(query.error as { status?: number })?.status === 404
                ? "這枚徽章沒有公開，或查驗連結已無法使用。"
                : "徽章暫時讀不到，請稍後再試。"}
            </p>
            <Button onClick={() => query.refetch()}>重新讀取</Button>
          </>
        ) : !badge ? (
          <p>正在查驗徽章…</p>
        ) : (
          <>
            <p className="text-lg font-bold">{badge.badge_name}</p>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-muted-foreground">玩家</dt>
                <dd>{badge.nickname}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">通過條件</dt>
                <dd>{badge.criteria}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">最近通過日</dt>
                <dd>{badge.last_passed_day}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">建議複測日</dt>
                <dd>{badge.suggested_retest_day}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">狀態</dt>
                <dd>
                  {badge.status === "retest_recommended"
                    ? "建議再次檢測，徽章仍有效"
                    : "已通過檢測"}
                </dd>
              </div>
            </dl>
          </>
        )}
      </section>
    </main>
  )
}
