/**
 * 詐騙類型的中文名稱,整個前端只用這一份。
 *
 * 必須與後端 `backend/app/core/fraud_types.py` 一致——練習重點的說明文字是後端寫的,
 * 畫面上的標籤若用另一套名字,玩家會以為是兩種不同的東西。
 * 原本收件匣用「網拍、交友、ATM」,前測雷達圖用「假網路購物、偽稱買賣」,
 * 而且雷達圖把 shopping 與 fake-sale 的名字對調了。
 */
export const FRAUD_TYPES = [
  "investment",
  "fake-sale",
  "shopping",
  "romance",
  "atm",
] as const

export const FRAUD_TYPE_LABELS: Record<string, string> = {
  investment: "投資詐騙",
  "fake-sale": "假網拍",
  shopping: "購物詐騙",
  romance: "假交友",
  atm: "解除分期",
}

export function fraudTypeLabel(slug: string): string {
  return FRAUD_TYPE_LABELS[slug] ?? "其他類型"
}
