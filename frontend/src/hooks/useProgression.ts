import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ProgressionService } from "@/client"

export function useProgression() {
  return useQuery({
    queryKey: ["progression", "me"],
    queryFn: () => ProgressionService.getMyProgression(),
    staleTime: 10_000,
  })
}

export function useRewardReceipt(receiptId: string | null | undefined) {
  return useQuery({
    queryKey: ["progression", "receipt", receiptId],
    queryFn: () =>
      ProgressionService.getRewardReceipt({ receiptId: receiptId! }),
    enabled: Boolean(receiptId),
    staleTime: Number.POSITIVE_INFINITY, // 收據不可變，永久快取
  })
}

export function usePurchaseUnlock() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (unlockKey: string) =>
      ProgressionService.purchaseUnlock({ unlockKey }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["progression", "me"] })
      queryClient.invalidateQueries({ queryKey: ["equipment"] })
    },
  })
}
