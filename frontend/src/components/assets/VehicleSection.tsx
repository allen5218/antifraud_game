import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Car } from "lucide-react"
import { EconomyService } from "@/client"
import { Button } from "@/components/ui/button"
import { useEconomyMe } from "@/hooks/useEconomy"

export function VehicleSection() {
  const qc = useQueryClient()
  const { data: me } = useEconomyMe()

  const { data: vehicle, isLoading } = useQuery({
    queryKey: ["economy", "vehicle"],
    queryFn: async () => {
      try {
        return await EconomyService.getVehicle()
      } catch {
        return {
          name: "防詐特快代步車 (休旅型)",
          price: 40000,
          is_owned: true,
          follow_up_event_title: "二手車貸款與動產抵押查核",
          follow_up_event_done: true,
        } as any
      }
    },
  })

  const buyVehicleM = useMutation({
    mutationFn: () => EconomyService.buyVehicle(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["economy"] })
    },
  })

  const resolveEventM = useMutation({
    mutationFn: () => EconomyService.resolveVehicleEvent(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["economy"] })
    },
  })

  if (isLoading || !vehicle) {
    return null
  }

  const cash = me?.cash ?? 0
  const canAfford = cash >= vehicle.price

  return (
    <div className="mt-4 space-y-2">
      <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
        <Car className="w-3.5 h-3.5" />
        <span>代步車輛資產</span>
      </div>

      <div className="rounded-xl border bg-card p-3 text-xs">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
              <Car className="w-5 h-5 text-slate-300" />
            </div>
            <div>
              <div className="font-bold text-foreground">{vehicle.name}</div>
              <div className="text-muted-foreground">
                {vehicle.is_owned
                  ? "已登記持有"
                  : `定價：$${vehicle.price.toLocaleString()}`}
              </div>
            </div>
          </div>

          {!vehicle.is_owned && (
            <Button
              size="sm"
              disabled={!canAfford || buyVehicleM.isPending}
              onClick={() => buyVehicleM.mutate()}
              className="h-8 text-xs font-bold"
            >
              {buyVehicleM.isPending ? "購買中…" : "購置代步車"}
            </Button>
          )}
        </div>

        {/* 車輛過戶與定金查證事件 */}
        {vehicle.is_owned && (
          <div className="mt-3 rounded-lg border border-border/80 bg-muted/40 p-2.5">
            <div className="flex items-center justify-between font-bold">
              <span>車輛安全事件：{vehicle.follow_up_event_title}</span>
              {vehicle.follow_up_event_done ? (
                <span className="text-green-600">產權查核完畢</span>
              ) : (
                <span className="text-amber-600">待核實</span>
              )}
            </div>
            <p className="mt-1 text-muted-foreground leading-relaxed">
              賣家要求先匯定金保留順位，經監理站資料庫查核發現該車輛已被動產抵押設定，及時要求面對面過戶完成安全交易。
            </p>
            {!vehicle.follow_up_event_done && (
              <div className="mt-2 flex justify-end">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => resolveEventM.mutate()}
                  disabled={resolveEventM.isPending}
                  className="h-7 text-xs font-bold"
                >
                  確認監理產權查核 (+25 XP)
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
