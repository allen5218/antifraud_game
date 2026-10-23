import type { SurveyQuestionPublic } from "@/client"

export const OTHER = "其他"

export type SurveyAnswers = Record<string, unknown>

/** 第一個還沒答完的必填題；都答完回傳 null。規則和後端 validate_answers 一樣 */
export function firstMissing(
  questions: SurveyQuestionPublic[],
  answers: SurveyAnswers,
): string | null {
  for (const q of questions) {
    const value = answers[q.id]
    if (!q.required) continue
    if (q.kind === "consent" && value !== true) return q.id
    if (q.kind === "single" && typeof value !== "string") return q.id
    if (q.kind === "multi" && (!Array.isArray(value) || value.length === 0))
      return q.id
    if (q.kind === "scale" && typeof value !== "number") return q.id
    if (q.kind === "text" && !(typeof value === "string" && value.trim()))
      return q.id
    if (q.other && choseOther(value) && !otherText(answers, q.id)) return q.id
  }
  return null
}

export function choseOther(value: unknown): boolean {
  return value === OTHER || (Array.isArray(value) && value.includes(OTHER))
}

function otherText(answers: SurveyAnswers, id: string): string {
  const text = answers[`${id}_other`]
  return typeof text === "string" ? text.trim() : ""
}

export function toggle(list: unknown, option: string): string[] {
  const current = Array.isArray(list) ? (list as string[]) : []
  return current.includes(option)
    ? current.filter((o) => o !== option)
    : [...current, option]
}

/** 依題目的段落分組，保持原本的順序 */
export function sections(
  questions: SurveyQuestionPublic[],
): { title: string; questions: SurveyQuestionPublic[] }[] {
  const groups: { title: string; questions: SurveyQuestionPublic[] }[] = []
  for (const q of questions) {
    const last = groups[groups.length - 1]
    if (last && last.title === q.section) last.questions.push(q)
    else groups.push({ title: q.section, questions: [q] })
  }
  return groups
}
