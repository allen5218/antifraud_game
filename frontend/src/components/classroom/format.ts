import { fraudTypeLabel } from "@/lib/fraudTypes"

export const STATUS_LABELS: Record<string, string> = {
  todo: "還沒做",
  done: "完成",
  late: "遲交完成",
  overdue: "已過期，還沒做",
}

export const KIND_LABELS: Record<string, string> = {
  comprehensive: "綜合檢測",
  specialized: "專項檢測",
  practice: "練習量",
  pretest: "入門前測",
}

export function percent(value: number | null | undefined): string {
  return value == null ? "沒有資料" : `${Math.round(value * 100)}%`
}

export function weakestSentence(
  weakest: string[],
  accuracy: { fraud_type: string; accuracy: number | null }[],
): string | null {
  if (weakest.length === 0) return null
  const value = accuracy.find((t) => t.fraud_type === weakest[0])?.accuracy
  return `全班最弱：${weakest.map(fraudTypeLabel).join("、")}（答對 ${percent(value)}）`
}

export function studentLabel(s: {
  student_number?: string | null
  student_name?: string | null
}): string {
  if (!s.student_number && !s.student_name) return "還沒填學號名字"
  return [s.student_number, s.student_name].filter(Boolean).join(" ")
}
