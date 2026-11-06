import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { EquipmentService } from "@/client"
import { equipmentActionKey } from "@/utils/progressionDisplay"

type EquipmentRef = { id: string; rank: number; rank_cap: number }

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
    mutationFn: (item: EquipmentRef) =>
      EquipmentService.upgradeItem({
        itemId: item.id,
        xIdempotencyKey: equipmentActionKey("upgrade", item),
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
    mutationFn: (item: EquipmentRef) =>
      EquipmentService.breakthroughItem({
        itemId: item.id,
        xIdempotencyKey: equipmentActionKey("breakthrough", item),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["equipment"] })
      queryClient.invalidateQueries({ queryKey: ["progression", "me"] })
    },
  })
}
