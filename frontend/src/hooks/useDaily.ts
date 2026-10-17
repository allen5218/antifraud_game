import { useQuery } from "@tanstack/react-query"
import { DailyService } from "@/client"

/**
 * 今天的每日訓練。第一次打開時後端才建立這個人今天的牌局並開始計時，
 * 所以只在每日訓練頁面呼叫（首頁不打，免得看一眼首頁就開始算時間）。
 * 作答與結算沿用訊息判讀的 useQuizAnswer／useQuizComplete。
 */
export function useDailyToday() {
  return useQuery({
    queryKey: ["daily", "today"],
    queryFn: () => DailyService.dailyToday(),
    staleTime: 0,
    // 離開頁面就丟掉快取：結算後再進來，不會先閃出結算前的作答畫面
    gcTime: 0,
    refetchOnWindowFocus: false,
    retry: false,
  })
}
