/** 結局 → 收件匣徽章。勾叉用 lucide 圖示畫,不寫在文字裡。 */
export const OUTCOME_BADGES: Record<
  string,
  { label: string; tone: "win" | "lose" }
> = {
  win_report: { label: "識破成功", tone: "win" },
  win_trust: { label: "正確信任", tone: "win" },
  lose_scammed: { label: "被騙了", tone: "lose" },
  lose_misreport: { label: "誤判好人", tone: "lose" },
}
