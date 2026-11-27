import { queryOptions, useQuery } from "@tanstack/react-query"
import { EconomyService } from "@/client"

// ── 錯誤處理輔助 ────────────────────────────────────────────────────────────────

export function extractErrorCode(err: unknown): string | undefined {
  const body = (err as { body?: unknown })?.body
  const detail = (body as { detail?: unknown })?.detail
  if (detail && typeof detail === "object" && "code" in detail) {
    return String((detail as { code: unknown }).code)
  }
  if (typeof detail === "string") return detail
  return undefined
}

// ── 查詢 ──────────────────────────────────────────────────────────────────────
// 查詢設定另外匯出，路由的 loader 預先載入時用同一把 key，進頁面就直接有資料。
// 房產、收租、升級卡都在放置經營（`useEstate.ts`）。

/** 當前使用者的錢、訓練等級與連續天數 */
export const economyMeQuery = queryOptions({
  queryKey: ["economy", "me"],
  queryFn: () => EconomyService.readMe(),
  staleTime: 30_000,
  refetchOnWindowFocus: true,
})

export function useEconomyMe() {
  return useQuery(economyMeQuery)
}
