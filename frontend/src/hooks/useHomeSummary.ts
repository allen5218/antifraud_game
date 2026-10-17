import { useQuery } from "@tanstack/react-query"
import { HomeService, type HomeSummary } from "@/client"

export type { HomeSummary }

export const HOME_SUMMARY_KEY = ["home-summary"] as const

export const homeApi = {
  summary: () => HomeService.homeSummary(),
}

export function useHomeSummary() {
  return useQuery({
    queryKey: HOME_SUMMARY_KEY,
    queryFn: () => homeApi.summary(),
    // 首頁彙整了每一頁都會改到的狀態（前測、練習、檢測、房產），
    // 靠各頁各自 invalidate 一定會漏，所以每次回到房間都重讀（這支 API 只讀不寫）。
    staleTime: 0,
    retry: false,
  })
}
