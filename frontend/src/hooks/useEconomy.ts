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

/** 當前使用者的經濟狀態（現金、等級、連勝天數、待領收益、破產旗標） */
export function useEconomyMe() {
  return useQuery({
    queryKey: ["economy", "me"],
    queryFn: EconomyService.readMe,
    staleTime: 30_000,
    refetchOnWindowFocus: true,
  })
}

/** 所有房產等級清單 + 已擁有清單 */
export function useProperties() {
  return useQuery({
    queryKey: ["economy", "properties"],
    queryFn: EconomyService.listProperties,
    staleTime: 30_000,
    refetchOnWindowFocus: true,
  })
}

/** 資產摘要（現金、房產總值、每日收益、總身家、持有數） */
export function useAssets() {
  return useQuery({
    queryKey: ["economy", "assets"],
    queryFn: EconomyService.getAssets,
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
    onError: () => showErrorToast("變賣失敗，請重試"),
  })
}
