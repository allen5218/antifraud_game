import {
  queryOptions,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { type EstatePublic, EstateService } from "@/client"
import { HOME_SUMMARY_KEY } from "./useHomeSummary"

export const ESTATE_KEY = ["estate"] as const

/**
 * 放置經營（分頁「經營」）。讀取時後端會把經理收的租金入帳，
 * 所以每 30 秒重讀一次，中間的租金由畫面自己往上加（`estateClock.ts`）。
 */
export const estateQuery = queryOptions({
  queryKey: ESTATE_KEY,
  queryFn: () => EstateService.readEstate(),
  staleTime: 10_000,
  refetchInterval: 30_000,
  refetchOnWindowFocus: true,
})

export function useEstate() {
  return useQuery(estateQuery)
}

/** 經營的變更都回傳整個經營畫面，直接換掉快取；錢與房間外觀也一起重讀 */
function useEstateMutation<T>(fn: (input: T) => Promise<EstatePublic>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: (data) => {
      queryClient.setQueryData(ESTATE_KEY, data)
      queryClient.invalidateQueries({ queryKey: ["economy"] })
      queryClient.invalidateQueries({ queryKey: HOME_SUMMARY_KEY })
    },
  })
}

export function useBuyIndustry() {
  return useEstateMutation(
    (v: { tierId: number; expectedOwned: number; count?: number }) =>
      EstateService.buyIndustry({
        tierId: v.tierId,
        requestBody: { expected_owned: v.expectedOwned, count: v.count ?? 1 },
      }),
  )
}

export function useCollectRent() {
  return useEstateMutation((tierId: number) =>
    EstateService.collectRent({ tierId }),
  )
}

export function useBuyCard() {
  return useEstateMutation((v: { tierId: number; expectedLevel: number }) =>
    EstateService.buyUpgradeCard({
      tierId: v.tierId,
      requestBody: { expected_level: v.expectedLevel },
    }),
  )
}

export function useAssignManager() {
  return useEstateMutation((v: { tierId: number; itemId: string | null }) =>
    EstateService.assignManager({
      tierId: v.tierId,
      requestBody: { item_id: v.itemId },
    }),
  )
}

export function useMoveHouse() {
  return useEstateMutation((expectedMoves: number) =>
    EstateService.moveHouse({ requestBody: { expected_moves: expectedMoves } }),
  )
}

export function useLegacySeen() {
  return useEstateMutation((_: undefined) => EstateService.legacyReportSeen())
}
