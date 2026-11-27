import type { EstatePublic, IndustryPublic } from "@/client"
import { parseBigIntSafe } from "@/utils/money"

/**
 * 兩次重讀之間，畫面自己把收租往前推：有經理的進度條一直跑、跑滿就把租金加到現金上；
 * 沒經理的跑滿就停在「收租」。真正的入帳以後端為準（每 30 秒重讀一次）。
 */
export type IndustryNow = {
  /** 這一輪走了幾成（0～1） */
  progress: number
  /** 沒有經理、已經跑滿在等玩家按 */
  ready: boolean
  /** 重讀之後畫面估計又收了多少 */
  earned: bigint
}

export function projectIndustry(
  ind: IndustryPublic,
  elapsedSeconds: number,
): IndustryNow {
  if (ind.owned <= 0 || ind.cycle_seconds <= 0) {
    return { progress: 0, ready: false, earned: 0n }
  }
  const at = ind.progress_seconds + Math.max(0, elapsedSeconds)
  if (!ind.manager) {
    const progress = Math.min(1, at / ind.cycle_seconds)
    return { progress, ready: progress >= 1, earned: 0n }
  }
  const cycles = Math.floor(at / ind.cycle_seconds)
  return {
    progress: (at % ind.cycle_seconds) / ind.cycle_seconds,
    ready: false,
    earned: BigInt(cycles) * parseBigIntSafe(ind.revenue_per_cycle),
  }
}

/** 畫面上的現金：後端給的現金加上重讀之後經理估計又收的 */
export function projectCash(
  estate: EstatePublic,
  elapsedSeconds: number,
): bigint {
  let cash = parseBigIntSafe(estate.cash)
  for (const ind of estate.industries) {
    cash += projectIndustry(ind, elapsedSeconds).earned
  }
  return cash
}
