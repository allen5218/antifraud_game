import type {
  ExamGate,
  ExamMessageAnswer,
  ExamPretestAnswer,
  ExamState,
  ExamSwipeAnswer,
} from "@/client"
import { fraudTypeLabel } from "@/lib/fraudTypes"

export type DraftAnswer =
  | ExamPretestAnswer
  | ExamSwipeAnswer
  | ExamMessageAnswer
/** 給玩家看的模式與類型。綜合檢測前測還沒定類型時，只寫「綜合檢測」。 */
export function examKindLabel(
  mode: string,
  fraudType: string | null | undefined,
): string {
  const name = mode === "specialized" ? "專項檢測" : "綜合檢測"
  if (!fraudType) return name
  return `${name}・${fraudTypeLabel(fraudType)}`
}
export function errorCode(error: unknown): string | undefined {
  return (error as { body?: { detail?: { code?: string } } } | null)?.body
    ?.detail?.code
}
export function examError(error: unknown): string {
  switch (errorCode(error)) {
    case "exam_in_progress":
      return "你還有一場檢測沒完成，請先繼續檢測。"
    case "exam_daily_limit":
      return "今天的檢測次數用完了，明天再來。"
    case "retake_gate":
      return "先完成補考練習，再回來檢測。"
    case "exam_unavailable":
      return "檢測題目還沒準備好，請稍後再試。"
    case "exam_not_found":
      return "找不到這場檢測，請回檢測頁查看。"
    case "exam_stage_required":
      return "關卡進度已更新，請重新讀取檢測。"
    case "exam_ended":
      return "檢測已結束，請重新讀取結果。"
    case "agent_failed":
      return "對方暫時無法回覆，這次不扣回覆次數，請再試一次。"
    case "turn_limit_reached":
      return "回覆次數用完了，請下判斷。"
    default:
      return "目前無法完成，請再試一次。"
  }
}
export function secondsLeft(expiresAt: string, now = Date.now()): number {
  return Math.max(0, Math.ceil((Date.parse(expiresAt) - now) / 1000))
}
export function gateRemaining(gate: ExamGate): string {
  if (gate.met) return "練習已完成，可以再檢測了。"
  const parts = (
    [
      ["滑卡", gate.swipe, "張"],
      ["訊息判讀", gate.quiz, "題"],
      ["情境對抗", gate.scenario, "場"],
    ] as const
  )
    .filter(([, count]) => count.done < count.need)
    .map(
      ([label, count, unit]) => `${label} ${count.need - count.done} ${unit}`,
    )
  const recent = Math.max(0, gate.recent.need - gate.recent.correct)
  return `${parts.length ? `還差${parts.join("、")}。` : "練習數量已足夠。"}${recent ? `最近十題還要答對 ${recent} 題。` : ""}`
}
const draftKey = (state: ExamState) => `exam-draft:${state.id}:${state.stage}`
export function saveDraft(state: ExamState, answers: DraftAnswer[]) {
  try {
    sessionStorage.setItem(draftKey(state), JSON.stringify(answers))
  } catch {
    /* 儲存空間不可用時仍可在本頁作答。 */
  }
}
export function clearDraft(state: ExamState) {
  try {
    sessionStorage.removeItem(draftKey(state))
  } catch {
    /* 不影響伺服器交卷。 */
  }
}
export function readDraft(state: ExamState): DraftAnswer[] {
  try {
    const answers: DraftAnswer[] = JSON.parse(
      sessionStorage.getItem(draftKey(state)) ?? "[]",
    )
    if (!Array.isArray(answers) || answers.length > state.stage_items.length)
      return []
    const valid = answers.every((answer, i) => {
      const item = state.stage_items[i]
      if (
        state.stage === "pretest" &&
        "question_text" in item &&
        "question_id" in answer
      ) {
        return (
          answer.question_id === item.id &&
          item.options.some((option) => option.key === answer.selected_option)
        )
      }
      if (
        state.stage === "swipe" &&
        "scenario" in item &&
        "card_id" in answer
      ) {
        return (
          answer.card_id === item.id &&
          typeof answer.guess_is_scam === "boolean"
        )
      }
      if (
        state.stage === "message" &&
        "item_id" in item &&
        "item_id" in answer &&
        answer.item_id === item.item_id
      ) {
        return item.kind === "verdict"
          ? typeof answer.guess_is_scam === "boolean"
          : Array.isArray(answer.tags) &&
              new Set(answer.tags).size === answer.tags.length &&
              answer.tags.every((tag) =>
                item.options?.some((option) => option.tag === tag),
              )
      }
      return false
    })
    return valid ? answers : []
  } catch {
    return []
  }
}
