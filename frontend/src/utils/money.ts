/**
 * 貨幣與大數安全處理工具庫 (BigInt / Decimal String)
 * 支援 PostgreSQL NUMERIC(78,0) 與大倍率數值成長
 */

const SUFFIXES: [bigint, string][] = [
  [10n ** 33n, "Dc"],
  [10n ** 30n, "No"],
  [10n ** 27n, "Oc"],
  [10n ** 24n, "Sp"],
  [10n ** 21n, "Sx"],
  [10n ** 18n, "Qi"],
  [10n ** 15n, "Qa"],
  [10n ** 12n, "T"],
  [10n ** 9n, "B"],
  [10n ** 6n, "M"],
  [10n ** 3n, "K"],
]

/**
 * 將各種格式轉為安全的 BigInt。
 * 若含有小數點（如 "123.45"）則取整數部分；空值或無效值回傳 0n。
 */
export function parseBigIntSafe(
  val: string | number | bigint | null | undefined,
): bigint {
  if (val === null || val === undefined) return 0n
  if (typeof val === "bigint") return val
  if (typeof val === "number") {
    if (Number.isNaN(val) || !Number.isFinite(val)) return 0n
    return BigInt(Math.trunc(val))
  }
  const trimmed = val.trim()
  if (!trimmed) return 0n

  // 若為十進位小數字串，取整數部分
  const integerPart = trimmed.split(".")[0]
  if (!integerPart || integerPart === "-" || integerPart === "+") return 0n

  try {
    return BigInt(integerPart)
  } catch {
    return 0n
  }
}

/**
 * 加總所有金額項目
 */
export function addMoney(
  ...vals: (string | number | bigint | null | undefined)[]
): bigint {
  return vals.reduce<bigint>((sum, v) => sum + parseBigIntSafe(v), 0n)
}

/**
 * 減法 a - b
 */
export function subMoney(
  a: string | number | bigint | null | undefined,
  b: string | number | bigint | null | undefined,
): bigint {
  return parseBigIntSafe(a) - parseBigIntSafe(b)
}

/**
 * 取絕對值
 */
export function absMoney(
  val: string | number | bigint | null | undefined,
): bigint {
  const b = parseBigIntSafe(val)
  return b < 0n ? -b : b
}

/**
 * 比較 a 與 b：a < b 回傳 -1，a === b 回傳 0，a > b 回傳 1
 */
export function compareMoney(
  a: string | number | bigint | null | undefined,
  b: string | number | bigint | null | undefined,
): number {
  const bigA = parseBigIntSafe(a)
  const bigB = parseBigIntSafe(b)
  if (bigA < bigB) return -1
  if (bigA > bigB) return 1
  return 0
}

export function isGreaterOrEqual(
  a: string | number | bigint | null | undefined,
  b: string | number | bigint | null | undefined,
): boolean {
  return compareMoney(a, b) >= 0
}

export function isGreaterThan(
  a: string | number | bigint | null | undefined,
  b: string | number | bigint | null | undefined,
): boolean {
  return compareMoney(a, b) > 0
}

export interface FormatMoneyOptions {
  abbreviated?: boolean
  decimals?: number
}

/**
 * 格式化貨幣數字。
 * 預設完整逗號分位（如 1,234,567）；
 * 若 abbreviated 為 true，則依千分位縮寫（如 1.23M、4.56B、7.89T…）。
 */
export function formatMoney(
  val: string | number | bigint | null | undefined,
  options: FormatMoneyOptions = {},
): string {
  const b = parseBigIntSafe(val)
  const isNegative = b < 0n
  const absB = isNegative ? -b : b

  if (options.abbreviated && absB >= 1000n) {
    for (const [threshold, suffix] of SUFFIXES) {
      if (absB >= threshold) {
        const decimals = options.decimals ?? 2
        // 計算小數：將數值乘上 10^decimals 後除以 threshold
        const scale = 10n ** BigInt(decimals)
        const scaled = (absB * scale) / threshold
        const integerPart = scaled / scale
        const fractionalPart = scaled % scale

        let formatted = integerPart.toString()
        if (decimals > 0 && fractionalPart > 0n) {
          const fracStr = fractionalPart
            .toString()
            .padStart(decimals, "0")
            .replace(/0+$/, "")
          if (fracStr.length > 0) {
            formatted += `.${fracStr}`
          }
        }
        return `${isNegative ? "-" : ""}${formatted}${suffix}`
      }
    }
  }

  // 完整顯示：利用 BigInt 原生 toLocaleString 或手動三位一逗點以防超大數
  const absStr = absB.toString()
  const withCommas = absStr.replace(/\B(?=(\d{3})+(?!\d))/g, ",")
  return `${isNegative ? "-" : ""}${withCommas}`
}
