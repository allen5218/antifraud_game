import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { EconomyService } from "@/client/sdk.gen"
import { PropertyCard } from "@/components/assets/PropertyCard"
import {
  extractErrorCode,
  useBuyProperty,
  useEconomyMe,
} from "@/hooks/useEconomy"
import { HOME_SUMMARY_KEY } from "@/hooks/useHomeSummary"
import { MascotCard } from "./MascotCard"
import { mascotApi } from "./mascotApi"

export function ShopPage() {
  const [tab, setTab] = useState<"mascot" | "property">("mascot")
  const [shortId, setShortId] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const list = useQuery({
    queryKey: ["mascot", "items"],
    queryFn: () => mascotApi.list(),
    retry: false,
  })
  const purchase = useMutation({
    mutationFn: (id: string) => mascotApi.purchase(id),
    onSuccess: () => {
      setShortId(null)
      queryClient.invalidateQueries({ queryKey: HOME_SUMMARY_KEY })
      queryClient.invalidateQueries({ queryKey: ["economy", "me"] })
      queryClient.invalidateQueries({ queryKey: ["mascot", "items"] })
    },
    onError: (err, id) => {
      if (extractErrorCode(err) === "insufficient_cash") setShortId(id)
    },
  })
  const display = useMutation({
    mutationFn: (id: string) => mascotApi.display(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: HOME_SUMMARY_KEY })
      queryClient.invalidateQueries({ queryKey: ["mascot", "items"] })
    },
  })
  const { data: me } = useEconomyMe()
  // 跟 useBuyProperty 同一把 query key，買完會一起刷新。
  const { data: properties } = useQuery({
    queryKey: ["economy", "properties"],
    queryFn: () => EconomyService.listProperties(),
    staleTime: 30_000,
  })
  const { mutate: buyProperty } = useBuyProperty()
  const cash = me?.cash ?? 0
  const level = me?.level ?? 1
  const ownedCount = new Map<number, number>()
  for (const owned of properties?.owned ?? []) {
    ownedCount.set(owned.tier.id, (ownedCount.get(owned.tier.id) ?? 0) + 1)
  }

  return (
    <div className="flex flex-col gap-4">
      <div
        role="tablist"
        aria-label="商店分類"
        className="grid grid-cols-2 gap-2"
      >
        <button
          type="button"
          role="tab"
          aria-selected={tab === "mascot"}
          onClick={() => setTab("mascot")}
          className={`rounded-xl px-3 py-2 text-sm font-bold ${
            tab === "mascot"
              ? "bg-primary text-primary-foreground"
              : "bg-surface-2 text-foreground"
          }`}
        >
          吉祥物
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "property"}
          onClick={() => setTab("property")}
          className={`rounded-xl px-3 py-2 text-sm font-bold ${
            tab === "property"
              ? "bg-primary text-primary-foreground"
              : "bg-surface-2 text-foreground"
          }`}
        >
          房產
        </button>
      </div>

      {tab === "mascot" ? (
        <div className="grid grid-cols-2 gap-3">
          {(list.data?.items ?? []).map((item) => (
            <MascotCard
              key={item.id}
              item={item}
              error={shortId === item.id ? "錢不夠" : undefined}
              pending={purchase.isPending || display.isPending}
              onBuy={() => purchase.mutate(item.id)}
              onDisplay={() => display.mutate(item.id)}
            />
          ))}
        </div>
      ) : (
        // 房產卡是橫的（圖、價格與日收入、按鈕），兩欄會把價格擠成好幾行，所以一欄
        <div className="grid grid-cols-1 gap-3">
          {(properties?.tiers ?? []).map((tier) => {
            const count = ownedCount.get(tier.id)
            return (
              <PropertyCard
                key={tier.id}
                tier={tier}
                count={count}
                locked={level < tier.unlock_level}
                affordable={cash >= tier.price}
                onBuy={() => buyProperty(tier.id)}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}
