/** 詐騙類型 → 收件匣標籤(短 chip 用) */
export const FRAUD_TYPE_LABELS: Record<string, string> = {
  investment: "投資",
  shopping: "購物",
  "fake-sale": "網拍",
  romance: "交友",
  atm: "ATM",
}

/** 結局 → 收件匣徽章 */
export const OUTCOME_BADGES: Record<
  string,
  { label: string; tone: "win" | "lose" }
> = {
  win_report: { label: "✓ 識破成功", tone: "win" },
  win_trust: { label: "✓ 正確信任", tone: "win" },
  lose_scammed: { label: "✗ 被騙了", tone: "lose" },
  lose_misreport: { label: "✗ 誤判好人", tone: "lose" },
}
