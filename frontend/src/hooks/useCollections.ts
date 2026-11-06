import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { CollectionsService } from "@/client"

export function useCollections() {
  return useQuery({
    queryKey: ["collections", "me"],
    queryFn: () => CollectionsService.readCollections(),
    staleTime: 10_000,
    retry: false,
  })
}

export function useGameplayAction() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (run: () => Promise<unknown>) => run(),
    onSuccess: async () => {
      await Promise.all(
        [
          "collections",
          "progression",
          "equipment",
          "economy",
          "seasons",
          "collection-board",
          "player",
          "home-summary",
        ].map((key) => client.invalidateQueries({ queryKey: [key] })),
      )
    },
  })
}
