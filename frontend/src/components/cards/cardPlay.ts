/** 卡片作答的純邏輯（填空切字、排順序、配對），畫面在 CardQuestion.tsx */

import type { Choice } from "@/client"

export const BLANK = "＿＿"

/** 一按就送出的題型；排順序、配對要排完再按「送出」 */
export const SINGLE_ANSWER_KINDS = new Set([
  "judge",
  "choice",
  "fill",
  "reply",
  "spot",
])

/** 題目切成空格前後兩段；沒有空格回 null */
export function splitBlank(prompt: string): [string, string] | null {
  const at = prompt.indexOf(BLANK)
  if (at < 0) return null
  return [prompt.slice(0, at), prompt.slice(at + BLANK.length)]
}

/** 排順序：點一下放到最後，再點一下拿回來 */
export function toggleStep(picked: string[], id: string): string[] {
  return picked.includes(id) ? picked.filter((x) => x !== id) : [...picked, id]
}

export interface MatchState {
  /** 左邊代號 → 右邊代號 */
  pairs: Record<string, string>
  /** 已經點了、還沒配的左邊 */
  pending: string | null
}

export const EMPTY_MATCH: MatchState = { pairs: {}, pending: null }

/** 點左邊：已經配好的就拆開，然後等著配右邊 */
export function tapLeft(state: MatchState, leftId: string): MatchState {
  const { [leftId]: _, ...rest } = state.pairs
  return { pairs: rest, pending: state.pending === leftId ? null : leftId }
}

/** 點右邊：有等著的左邊就配起來；這個右邊原本配給別人的話先拆開 */
export function tapRight(state: MatchState, rightId: string): MatchState {
  const pairs = Object.fromEntries(
    Object.entries(state.pairs).filter(([, r]) => r !== rightId),
  )
  if (state.pending === null) return { pairs, pending: null }
  return { pairs: { ...pairs, [state.pending]: rightId }, pending: null }
}

/** 全部配好時，照左邊的順序列出右邊代號；還沒配完回 null */
export function matchAnswer(
  left: Choice[],
  pairs: Record<string, string>,
): string[] | null {
  const ids = left.map((l) => pairs[l.id])
  return ids.every(Boolean) ? ids : null
}
