import type { CohortProgressMember, CohortPublic } from "@/client"

export const TAIPEI = "Asia/Taipei"

/** 到期時間顯示成台灣日期，例如 2026/11/2 */
export function taipeiDate(iso: string): string {
  return new Date(iso).toLocaleDateString("zh-TW", { timeZone: TAIPEI })
}

export function taipeiTime(iso: string | null | undefined): string {
  if (!iso) return "尚無資料"
  return new Date(iso).toLocaleString("zh-TW", {
    timeZone: TAIPEI,
    hour12: false,
  })
}

/** 日期欄位的值（YYYY-MM-DD，台灣時間） */
export function dateInputValue(iso: string | null | undefined): string {
  if (!iso) return ""
  return new Date(iso).toLocaleDateString("sv-SE", { timeZone: TAIPEI })
}

/** 選的那天的台灣時間 23:59:59 到期 */
export function expiryOf(date: string): string {
  return `${date}T23:59:59+08:00`
}

export function limitText(cohort: CohortPublic): string {
  const quota =
    cohort.max_members == null ? "名額不限" : `名額 ${cohort.max_members} 人`
  const expiry = cohort.expires_at
    ? `${taipeiDate(cohort.expires_at)} 到期`
    : "不限期限"
  return `已加入 ${cohort.member_count ?? 0} 人・${quota}・${expiry}`
}

export function seconds(value: number | null | undefined): string {
  if (value == null) return "沒有計時"
  if (value < 60) return `${value} 秒`
  return `${Math.floor(value / 60)} 分 ${value % 60} 秒`
}

export function pretestText(m: CohortProgressMember): string {
  return m.pretest_done
    ? `答對 ${m.pretest_correct}／${m.pretest_total}・${seconds(m.pretest_seconds)}`
    : "沒做"
}

export function examText(m: CohortProgressMember): string {
  return m.exam_completed
    ? `${m.best_exam_score} 分・最久 ${seconds(m.exam_seconds)}`
    : "沒交卷"
}

export function surveyText(m: CohortProgressMember): string {
  return m.survey_done
    ? `${seconds(m.survey_seconds)}・注意力題${m.survey_attention_ok ? "對" : "錯"}`
    : "沒填"
}

export const EXAM_MODE_LABELS: Record<string, string> = {
  comprehensive: "綜合檢測",
  specialized: "專項檢測",
}

export const EXAM_STATUS_LABELS: Record<string, string> = {
  active: "進行中",
  completed: "交卷",
  expired: "時間到",
  abandoned: "放棄",
  voided: "作廢",
}

export const EXAM_STAGE_LABELS: Record<string, string> = {
  pretest: "前測",
  swipe: "滑卡",
  message: "訊息判讀",
  scenario: "情境對抗",
}

export const PRACTICE_MODE_LABELS: Record<string, string> = {
  swipe: "滑卡",
  quiz: "訊息判讀",
  scenario: "情境對抗",
}
