import { useQuery } from "@tanstack/react-query"
import { SeasonsService } from "@/client"

export type BoardKind = "accuracy" | "speed" | "power"

export function useSeasonCurrent() {
  return useQuery({
    queryKey: ["seasons", "current"],
    queryFn: () => SeasonsService.getSeasonCurrent(),
    staleTime: 30_000,
  })
}

export function useSeasonBoard(seasonId: string | undefined, board: BoardKind) {
  return useQuery({
    queryKey: ["seasons", seasonId, "board", board],
    queryFn: () =>
      SeasonsService.getBoard({
        seasonId: seasonId!,
        board,
      }),
    enabled: Boolean(seasonId),
    staleTime: 30_000,
  })
}
