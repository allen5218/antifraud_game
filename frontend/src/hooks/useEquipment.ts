import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { EquipmentService } from "@/client"

export function useEquipment() {
  return useQuery({
    queryKey: ["equipment"],
    queryFn: () => EquipmentService.listEquipment(),
    staleTime: 10_000,
  })
}

export function useUpdateLoadout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (itemIds: string[]) =>
      EquipmentService.updateLoadout({
        requestBody: {
          items: itemIds.map((itemId, idx) => ({
            slot_index: idx,
            item_id: itemId,
          })),
          expected_revision: queryClient.getQueryData<{ revision: number }>([
            "equipment",
          ])?.revision,
        },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["equipment"] })
      queryClient.invalidateQueries({ queryKey: ["progression", "me"] })
    },
  })
}

export function useUpgradeEquipment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (itemId: string) =>
      EquipmentService.upgradeItem({
        itemId,
        xIdempotencyKey: crypto.randomUUID(),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["equipment"] })
      queryClient.invalidateQueries({ queryKey: ["progression", "me"] })
      queryClient.invalidateQueries({ queryKey: ["economy"] })
    },
  })
}

export function useBreakthroughEquipment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (itemId: string) =>
      EquipmentService.breakthroughItem({
        itemId,
        xIdempotencyKey: crypto.randomUUID(),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["equipment"] })
      queryClient.invalidateQueries({ queryKey: ["progression", "me"] })
    },
  })
}
