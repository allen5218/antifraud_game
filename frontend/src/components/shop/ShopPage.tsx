import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Building2 } from "lucide-react"
import { useEffect, useState } from "react"
import { onboardingApi } from "@/components/room/onboardingApi"
import { Skeleton } from "@/components/ui/skeleton"
import { extractErrorCode } from "@/hooks/useEconomy"
import { HOME_SUMMARY_KEY } from "@/hooks/useHomeSummary"
import { MascotCard } from "./MascotCard"
import { mascotApi, mascotItemsQuery } from "./mascotApi"

/** 商店：買吉祥物。買到的吉祥物可以在分頁「經營」派去當經理；房產在經營裡買 */
export function ShopPage() {
  const [shortId, setShortId] = useState<string | null>(null)
  const queryClient = useQueryClient()
  // 新手任務「去購物看看」：進來就算看過；記不到也不影響購物
  useEffect(() => {
    onboardingApi
      .shopVisited()
      .then(() => queryClient.invalidateQueries({ queryKey: HOME_SUMMARY_KEY }))
      .catch(() => {})
  }, [queryClient])
  const list = useQuery(mascotItemsQuery)
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
  return (
    <div className="flex flex-col gap-4">
      <p className="flex items-center gap-2 rounded-xl bg-surface-2 px-3 py-2 text-sm">
        <Building2 aria-hidden className="size-4 text-primary" />
        買來的吉祥物可以派去當經理，自動幫房產收租。房產在「經營」買。
      </p>
      <div className="grid grid-cols-2 gap-3">
        {list.isPending &&
          [0, 1, 2, 3].map((n) => (
            <Skeleton key={n} className="aspect-[3/4] w-full rounded-xl" />
          ))}
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
    </div>
  )
}
