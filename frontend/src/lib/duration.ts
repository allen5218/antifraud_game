/** 秒數轉成「1 分 05 秒」「42 秒」這種白話寫法 */
export function formatDuration(seconds: number): string {
  const safe = Math.max(0, Math.round(seconds))
  const minutes = Math.floor(safe / 60)
  const rest = safe % 60
  if (minutes === 0) return `${rest} 秒`
  return `${minutes} 分 ${String(rest).padStart(2, "0")} 秒`
}
