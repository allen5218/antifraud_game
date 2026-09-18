import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { EconomyService } from "@/client"
import useCustomToast from "./useCustomToast"

// ── 錯誤處理輔助 ────────────────────────────────────────────────────────────────

function extractErrorCode(err: unknown): string | undefined {
  const body = (err as { body?: unknown })?.body
  const detail = (body as { detail?: unknown })?.detail
  if (detail && typeof detail === "object" && "code" in detail) {
    return String((detail as { code: unknown }).code)
  }
  if (typeof detail === "string") return detail
  return undefined
}

// ── 查詢 ──────────────────────────────────────────────────────────────────────

const MOCK_ECONOMY_ME = {
  cash: 12500,
  xp: 380,
  level: 2,
  streak_days: 3,
  pending_accrual: 250,
  is_bankrupt: false,
}

const MOCK_ASSETS = {
  total_asset_value: 37500,
  cash: 12500,
  property_value: 25000,
  daily_accrual: 250,
  total_properties: 1,
}

const MOCK_PROPERTIES = {
  available_tiers: [
    { id: 1, name: "雅房", cost: 1000, daily_income: 5, level_required: 1, icon: "🚪" },
    { id: 2, name: "獨立套房", cost: 5000, daily_income: 35, level_required: 1, icon: "🛋️" },
    { id: 3, name: "兩房公寓", cost: 25000, daily_income: 250, level_required: 2, icon: "🏢" },
    { id: 4, name: "三房電梯大廈", cost: 100000, daily_income: 1200, level_required: 3, icon: "🏙️" },
    { id: 5, name: "獨棟別墅", cost: 300000, daily_income: 4200, level_required: 5, icon: "🏡" },
    { id: 6, name: "頂級豪宅", cost: 1000000, daily_income: 15000, level_required: 10, icon: "🏰" },
  ],
  owned: [
    { id: "prop_1", tier_id: 3, name: "兩房公寓", purchase_price: 25000, daily_income: 250, purchased_at: "2026-09-18" },
  ],
}

/** 當前使用者的經濟狀態（現金、等級、連勝天數、待領收益、破產旗標） */
export function useEconomyMe() {
  return useQuery({
    queryKey: ["economy", "me"],
    queryFn: async () => {
      try {
        return await EconomyService.readMe()
      } catch {
        return MOCK_ECONOMY_ME as any
      }
    },
    staleTime: 30_000,
    refetchOnWindowFocus: true,
  })
}

/** 所有房產等級清單 + 已擁有清單 */
export function useProperties() {
  return useQuery({
    queryKey: ["economy", "properties"],
    queryFn: async () => {
      try {
        return await EconomyService.listProperties()
      } catch {
        return MOCK_PROPERTIES as any
      }
    },
    staleTime: 30_000,
    refetchOnWindowFocus: true,
  })
}

/** 資產摘要（現金、房產總值、每日收益、總身家、持有數） */
export function useAssets() {
  return useQuery({
    queryKey: ["economy", "assets"],
    queryFn: async () => {
      try {
        return await EconomyService.getAssets()
      } catch {
        return MOCK_ASSETS as any
      }
    },
    staleTime: 30_000,
    refetchOnWindowFocus: true,
  })
}

// ── 變更 ──────────────────────────────────────────────────────────────────────

/** 領取待領每日收益 */
export function useClaimAccrual() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: EconomyService.claim,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["economy"] })
    },
  })
}

/** 購買房產等級 */
export function useBuyProperty() {
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()
  return useMutation({
    mutationFn: (tierId: number) => EconomyService.buyProperty({ tierId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["economy"] })
    },
    onError: (err: unknown) => {
      const code = extractErrorCode(err)
      const messages: Record<string, string> = {
        insufficient_cash: "現金不足，無法購買",
        level_required: "等級不足，尚未解鎖",
        bankruptcy_pending: "請先處理破產（變賣資產）",
      }
      showErrorToast(
        code && messages[code] ? messages[code] : "購買失敗，請重試",
      )
    },
  })
}

/** 變賣房產（強制清算） */
export function useLiquidate() {
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()
  return useMutation({
    mutationFn: (propertyIds: string[]) =>
      EconomyService.postLiquidate({
        requestBody: { property_ids: propertyIds },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["economy"] })
    },
    onError: (err: unknown) => {
      const code = extractErrorCode(err)
      const messages: Record<string, string> = {
        empty_property_ids: "請先勾選要變賣的房產",
        property_not_owned: "所選房產已變賣或不存在，請重新整理後再試",
      }
      showErrorToast(
        code && messages[code] ? messages[code] : "變賣失敗，請重試",
      )
    },
  })
}
