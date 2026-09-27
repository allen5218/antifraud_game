import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { LeaderboardService } from "@/client"

export type LeaderboardPeriod = "today" | "week"

export function useLeaderboard(period: LeaderboardPeriod) {
  return useQuery({
    queryKey: ["leaderboard", period],
    queryFn: () => LeaderboardService.readLeaderboard({ period }),
    staleTime: 30_000,
    retry: false,
  })
}

/** 設定或清除（空字串）排行榜暱稱 */
export function useUpdateNickname() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (nickname: string) =>
      LeaderboardService.updateNickname({ requestBody: { nickname } }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leaderboard"] })
    },
  })
}
