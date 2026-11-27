import { parseBigIntSafe } from "@/utils/money"

type MoneyLike = string | number | bigint | null | undefined

// 中文的大數單位（不夾英文的 K、M、B）
const UNITS: [bigint, string][] = [
  [10n ** 48n, "極"],
  [10n ** 44n, "載"],
  [10n ** 40n, "正"],
  [10n ** 36n, "澗"],
  [10n ** 32n, "溝"],
  [10n ** 28n, "穰"],
  [10n ** 24n, "秭"],
  [10n ** 20n, "垓"],
  [10n ** 16n, "京"],
  [10n ** 12n, "兆"],
  [10n ** 8n, "億"],
  [10n ** 4n, "萬"],
]

function withCommas(n: bigint): string {
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",")
}

/** 錢：一萬以下照寫（1,234），以上換成萬、億、兆…，最多三位有效數字（12.3 萬） */
export function formatYuan(value: MoneyLike): string {
  const n = parseBigIntSafe(value)
  const negative = n < 0n
  const abs = negative ? -n : n
  const sign = negative ? "-" : ""
  if (abs < 10_000n) return `${sign}${withCommas(abs)}`
  for (const [unit, name] of UNITS) {
    if (abs >= unit) {
      const whole = abs / unit
      if (whole >= 10_000n) return `${sign}${withCommas(whole)} ${name}`
      const digits = whole.toString().length
      const decimals = Math.max(0, 3 - digits)
      if (decimals === 0) return `${sign}${whole} ${name}`
      const scale = 10n ** BigInt(decimals)
      const scaled = (abs * scale) / unit
      const frac = (scaled % scale)
        .toString()
        .padStart(decimals, "0")
        .replace(/0+$/, "")
      return `${sign}${whole}${frac ? `.${frac}` : ""} ${name}`
    }
  }
  return `${sign}${withCommas(abs)}`
}

/** 每小時收入換成每秒（小數一位），例如 600 → 「0.2」 */
export function perSecond(perHour: MoneyLike): string {
  const tenths = (parseBigIntSafe(perHour) * 10n) / 3600n
  if (tenths < 100_000n) {
    const whole = tenths / 10n
    const frac = tenths % 10n
    return frac === 0n ? withCommas(whole) : `${withCommas(whole)}.${frac}`
  }
  return formatYuan(tenths / 10n)
}

/** 收租秒數寫成「6 秒」「2 分鐘」「4 小時」 */
export function formatCycle(seconds: number): string {
  if (seconds < 60) return `${seconds} 秒`
  if (seconds < 3600) return `${Math.round(seconds / 60)} 分鐘`
  const hours = seconds / 3600
  return Number.isInteger(hours) ? `${hours} 小時` : `${hours.toFixed(1)} 小時`
}

/** 離開多久：「3 小時 20 分」「45 分鐘」 */
export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h >= 24) return `${Math.floor(h / 24)} 天 ${h % 24} 小時`
  if (h > 0) return m > 0 ? `${h} 小時 ${m} 分` : `${h} 小時`
  return `${Math.max(1, m)} 分鐘`
}
