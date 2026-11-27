import {
  queryOptions,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { CardsService } from "@/client"
import { HOME_SUMMARY_KEY } from "@/hooks/useHomeSummary"

/** 首頁統計（今日目標、連續天數、學會幾招、各類進度），唯讀，可以放進 loader */
export const cardSummaryQuery = queryOptions({
  queryKey: ["cards", "summary"],
  queryFn: () => CardsService.cardSummary(),
})

/**
 * 發一輪（會建立牌局，不要放進 loader）。用查詢而不是變更：開發模式 StrictMode 會把
 * 元件掛兩次，掛載時送出的變更結果會被丟掉；查詢會合併成一次、結果照常回來。
 * `round` 換數字就是再發一輪。
 */
export function useCardRound(topic: string | null, round: number) {
  return useQuery({
    queryKey: ["cards", "round", topic, round],
    queryFn: () => CardsService.startRound({ requestBody: { topic } }),
    staleTime: Number.POSITIVE_INFINITY,
    gcTime: 0,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  })
}

export function useAnswerCard() {
  return useMutation({
    mutationFn: (vars: { roundId: string; cardKey: string; ids: string[] }) =>
      CardsService.answerCard({
        roundId: vars.roundId,
        requestBody: { card_key: vars.cardKey, ids: vars.ids },
      }),
  })
}

export function useCompleteRound() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (roundId: string) => CardsService.completeRound({ roundId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cardSummaryQuery.queryKey })
      queryClient.invalidateQueries({ queryKey: HOME_SUMMARY_KEY })
      queryClient.invalidateQueries({ queryKey: ["economy"] })
    },
  })
}
