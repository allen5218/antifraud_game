/** 倍率顯示：後端給的是完整精確小數，畫面只需要大概的大小。 */
export function formatFactor(value: string | null | undefined): string {
  const n = Number.parseFloat(value ?? "")
  if (!Number.isFinite(n) || n <= 0) return "1"
  const digits = n >= 1000 ? 0 : n >= 10 ? 1 : 2
  return n.toLocaleString("en-US", { maximumFractionDigits: digits })
}

/**
 * 強化／突破的重送鑰匙：依「從哪一階開始」產生，網路斷掉重按時後端認得是同一筆，
 * 不會再扣一次錢；成功升階後階數變了才換新鑰匙。
 */
export function equipmentActionKey(
  kind: "upgrade" | "breakthrough",
  item: { id: string; rank: number; rank_cap: number },
): string {
  return kind === "upgrade"
    ? `${item.id}:r${item.rank}`
    : `${item.id}:c${item.rank_cap}`
}
