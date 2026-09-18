import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { EconomyService } from "@/client"
import { Button } from "@/components/ui/button"

export function MyHomeSection() {
  const qc = useQueryClient()

  const { data: home, isLoading } = useQuery({
    queryKey: ["economy", "home"],
    queryFn: async () => {
      try {
        return await EconomyService.getMyHome()
      } catch {
        return {
          has_house: true,
          best_tier_name: "兩房公寓",
          house_count: 1,
          decorations: [
            { id: "d1", name: "防詐警惕植物", icon: "🪴", cost: 500, is_owned: true, is_equipped: true },
            { id: "d2", name: "智能安防監視器", icon: "📹", cost: 1200, is_owned: false, is_equipped: false },
            { id: "d3", name: "防詐大師紀念獎座", icon: "🏆", cost: 3000, is_owned: true, is_equipped: true },
          ],
          follow_up_event_unlocked: true,
          follow_up_event_title: "假冒社區公務維修",
          follow_up_event_done: false,
        } as any
      }
    },
  })

  const buyDecorM = useMutation({
    mutationFn: (decorId: string) =>
      EconomyService.buyHomeDecor({ requestBody: { decor_id: decorId } }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["economy"] })
    },
  })

  const toggleDecorM = useMutation({
    mutationFn: (decorId: string) =>
      EconomyService.toggleHomeDecor({ requestBody: { decor_id: decorId } }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["economy", "home"] })
    },
  })

  const resolveEventM = useMutation({
    mutationFn: () => EconomyService.resolveHomeEvent(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["economy"] })
    },
  })

  if (isLoading || !home || !home.has_house) {
    return null
  }

  return (
    <div className="mt-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
          🏡 我的家園與生活裝飾
        </div>
        <span className="text-xs text-muted-foreground">
          主宅：{home.best_tier_name ?? "自住宅"}（共 {home.house_count}{" "}
          筆房產）
        </span>
      </div>

      {/* 裝飾品展示櫃 */}
      <div className="grid grid-cols-3 gap-2">
        {home.decorations.map((d: { id: string; icon: string; name: string; cost: number; is_owned: boolean; is_equipped: boolean }) => (
          <div
            key={d.id}
            className={`flex flex-col items-center rounded-xl border p-2.5 text-center transition-colors ${
              d.is_equipped
                ? "border-primary bg-primary/5 ring-1 ring-primary"
                : "border-border bg-card"
            }`}
          >
            <div className="text-2xl">{d.icon}</div>
            <div className="mt-1 font-bold text-xs">{d.name}</div>
            <div className="text-[10px] text-muted-foreground">{d.cost} 💰</div>
            <div className="mt-2 w-full">
              {d.is_owned ? (
                <Button
                  size="sm"
                  variant={d.is_equipped ? "default" : "outline"}
                  onClick={() => toggleDecorM.mutate(d.id)}
                  disabled={toggleDecorM.isPending}
                  className="h-6 w-full text-[10px]"
                >
                  {d.is_equipped ? "展示中" : "點擊擺放"}
                </Button>
              ) : (
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => buyDecorM.mutate(d.id)}
                  disabled={buyDecorM.isPending}
                  className="h-6 w-full text-[10px]"
                >
                  購買
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* 社區公共修繕事件 */}
      {home.follow_up_event_unlocked && (
        <div className="rounded-xl border border-amber-300/60 bg-amber-500/5 p-3 text-xs">
          <div className="flex items-center justify-between font-bold text-amber-900 dark:text-amber-200">
            <span>🛠️ 社區生活事件：{home.follow_up_event_title}</span>
            {home.follow_up_event_done ? (
              <span className="text-green-600">✓ 已查證排除</span>
            ) : (
              <span className="text-amber-600">未結案</span>
            )}
          </div>
          <p className="mt-1 text-muted-foreground leading-relaxed">
            自稱社區合作工班上門催繳外牆修繕材料費，向管理中心查證確認並未招標該項工程，避免被假冒工班騙取數千元。
          </p>
          {!home.follow_up_event_done && (
            <div className="mt-2 flex justify-end">
              <Button
                size="sm"
                onClick={() => resolveEventM.mutate()}
                disabled={resolveEventM.isPending}
                className="h-7 text-xs font-bold"
              >
                核實管委會公告並結案 (+20 XP)
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
