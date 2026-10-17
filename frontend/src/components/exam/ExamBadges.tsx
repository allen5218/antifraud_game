import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Award } from "lucide-react"
import { QRCodeSVG } from "qrcode.react"
import type { ExamBadgePublic } from "@/client"
import { BadgesService } from "@/client/sdk.gen"
import { Button } from "@/components/ui/button"

export function ExamBadges({ badges }: { badges: ExamBadgePublic[] }) {
  // 檢測結果內的徽章是獲獎當下的快照，公開設定要另外讀目前狀態。
  const live = useQuery({
    queryKey: ["exam", "badges"],
    queryFn: () => BadgesService.ownBadges(),
    enabled: badges.length > 0,
    retry: false,
    staleTime: 0,
  })
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-bold">我的徽章</h2>
      {!badges.length && (
        <p className="text-sm text-muted-foreground">
          還沒有徽章，檢測達七十分就能獲得。
        </p>
      )}
      {badges.map((badge) => {
        const current = live.data?.find((value) => value.id === badge.id)
        return current && !live.isError ? (
          <Badge key={badge.id} badge={current} />
        ) : (
          <article key={badge.id} className="rounded-2xl border bg-card p-4">
            <h3 className="font-bold">{badge.name}</h3>
            <p
              className="mt-2 text-sm"
              role={live.isError ? "alert" : undefined}
            >
              {live.isError
                ? "目前的公開設定讀不到，請重新讀取。"
                : live.isPending
                  ? "正在讀取公開設定…"
                  : "找不到目前的徽章設定，請重新讀取。"}
            </p>
            {!live.isPending && (
              <Button variant="outline" onClick={() => live.refetch()}>
                重新讀取徽章
              </Button>
            )}
          </article>
        )
      })}
    </section>
  )
}
function Badge({ badge }: { badge: ExamBadgePublic }) {
  const qc = useQueryClient()
  const toggle = useMutation({
    mutationFn: (isPublic: boolean) =>
      BadgesService.updateBadge({
        badgeId: badge.id,
        requestBody: { is_public: isPublic },
      }),
    onSuccess: (updated) => {
      qc.setQueryData<ExamBadgePublic[]>(["exam", "badges"], (old) =>
        old?.map((value) => (value.id === updated.id ? updated : value)),
      )
      return qc.invalidateQueries({ queryKey: ["exam"] })
    },
  })
  const current = badge
  const url =
    current.is_public && current.public_slug
      ? `${window.location.origin}/badge/${encodeURIComponent(current.public_slug)}`
      : null
  return (
    <article className="rounded-2xl border bg-card p-4">
      <h3 className="flex items-center gap-2 font-bold">
        <Award aria-hidden className="size-5 text-warning" />
        {current.name}
      </h3>
      <p className="mt-2 text-xs text-muted-foreground">
        {/* en-CA 輸出 YYYY-MM-DD，和建議複測日、公開查驗頁同一種寫法 */}
        最近通過：
        {new Date(current.last_passed_at).toLocaleDateString("en-CA", {
          timeZone: "Asia/Taipei",
        })}
        。建議複測：{current.suggested_retest_at}。
      </p>
      <label className="mt-3 flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={current.is_public}
          disabled={toggle.isPending}
          onChange={(e) => toggle.mutate(e.target.checked)}
        />
        公開這枚徽章
      </label>
      {toggle.isError && (
        <p role="alert" className="mt-2 text-sm text-scam">
          公開設定沒有儲存成功，請再試一次。
        </p>
      )}
      {url && (
        <div className="mt-3 space-y-3">
          <a
            href={url}
            className="block break-all text-sm text-primary underline"
          >
            {url}
          </a>
          {/* QR code 固定黑格白底：深色模式的反色碼很多手機掃不出來，這是只用主題色的例外 */}
          <div className="w-fit rounded-xl bg-white p-3">
            <QRCodeSVG
              value={url}
              title={`${current.name}查驗連結`}
              size={160}
              marginSize={2}
              bgColor="#ffffff"
              fgColor="#000000"
            />
          </div>
        </div>
      )}
    </article>
  )
}
