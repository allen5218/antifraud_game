/**
 * 出生年：長輩常用民國年，所以民國、西元都收，一律換成西元送後端。
 * 範圍要和後端 `app/core/age.py` 一致（1900 年到今年減 5 歲）。
 */

export const MIN_BIRTH_YEAR = 1900
const MIN_AGE = 5
const ROC_OFFSET = 1911

export const BIRTH_YEAR_HINT = "民國或西元都可以，例如 64 或 1975"

/** 台灣時間的今年（台灣沒有日光節約時間，固定 UTC+8） */
export function taipeiYear(now: Date = new Date()): number {
  return new Date(now.getTime() + 8 * 60 * 60 * 1000).getUTCFullYear()
}

/** 把輸入換成西元出生年；看不懂或不合理回 null */
export function parseBirthYear(
  input: string,
  thisYear: number = taipeiYear(),
): number | null {
  const text = input.trim().replace(/^民國/, "").replace(/年$/, "").trim()
  if (!/^\d{1,4}$/.test(text)) return null
  const value = Number(text)
  const latest = thisYear - MIN_AGE
  // 三位數以內當民國年（民國 1 年到今年），四位數當西元
  const year = text.length <= 3 ? value + ROC_OFFSET : value
  if (year < MIN_BIRTH_YEAR || year > latest) return null
  return year
}
