import { type QueryClient, useQuery } from "@tanstack/react-query"
import { PracticeService } from "@/client"

const PRACTICE_PROFILE_KEY = ["practice", "profile"]

/**
 * 練習重點:目前最該加強哪一類、五類的出題比例、給玩家看的一句說明。
 *
 * 後端在每輪結算「之後」才在背景重新分析(可能要呼叫 Gemini 幾秒),
 * 所以結算當下拿到的常常是舊的。每次進頁面都重抓(staleTime 0),
 * 結算後再由 refreshPracticeProfileSoon 分幾次重抓。
 */
export function usePracticeProfile() {
  return useQuery({
    queryKey: PRACTICE_PROFILE_KEY,
    queryFn: () => PracticeService.readProfile(),
    staleTime: 0,
    refetchOnWindowFocus: false,
  })
}

/** 分析通常 3–5 秒,最慢到逾時約 20 秒;之後就不再重抓。 */
const REFRESH_DELAYS_MS = [0, 4000, 10000, 22000]

/**
 * 每輪結算後呼叫:畫面上有練習重點(首頁、結算卡)就會在分析完成後換成新的。
 * 沒有掛著的查詢只會被標成過期,下次進頁面時才重抓。
 */
export function refreshPracticeProfileSoon(qc: QueryClient) {
  for (const delay of REFRESH_DELAYS_MS) {
    setTimeout(
      () => qc.invalidateQueries({ queryKey: PRACTICE_PROFILE_KEY }),
      delay,
    )
  }
}
