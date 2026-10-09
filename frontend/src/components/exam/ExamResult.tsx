import { Link } from "@tanstack/react-router"
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts"
import type { ExamState } from "@/client"
import { FRAUD_TYPES, fraudTypeLabel } from "@/lib/fraudTypes"
import { ExamBadges } from "./ExamBadges"

export function ExamResult({ state }: { state: ExamState }) {
  const result = state.result
  if (state.status === "voided")
    return (
      <section className="space-y-4 rounded-2xl border bg-card p-5">
        <h1 className="text-xl font-bold">這次檢測不計次</h1>
        <p>對方無法正常回覆，這次不計分、不算檢測次數，也不用補考練習。</p>
        <Link to="/exam" className="text-primary underline">
          回檢測頁
        </Link>
      </section>
    )
  if (!result) return <p role="alert">結果讀不到，請重新讀取。</p>
  return (
    <div className="space-y-5">
      <section className="rounded-2xl border bg-card p-5 text-center">
        <h1 className="text-xl font-bold">
          {result.passed ? "檢測通過" : "這次沒有通過"}
        </h1>
        <p className="my-3 text-4xl font-extrabold">{result.total_score} 分</p>
        <p>
          {result.mode === "comprehensive" ? "綜合檢測" : "專項檢測"}・
          {fraudTypeLabel(result.fraud_type)}
        </p>
        {state.status === "expired" && (
          <p className="mt-2 text-sm text-muted-foreground">
            檢測時間到了，未交的關卡以零分計算。
          </p>
        )}
        {state.status === "abandoned" && (
          <p className="mt-2 text-sm text-muted-foreground">
            你已放棄這次檢測，算一次沒過。
          </p>
        )}
        {/* 專項檢測沒有前測，三關合計就是總分，不再重複 */}
        {result.mode === "comprehensive" && (
          <p className="mt-3 text-sm">
            弱項關卡合計：{result.weakness_score}／{result.weakness_max} 分
          </p>
        )}
      </section>
      {result.pretest_by_type && (
        <section className="rounded-2xl border bg-card p-4">
          <h2 className="font-bold">前測五類答對題數</h2>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart
              data={FRAUD_TYPES.map((type) => ({
                type: fraudTypeLabel(type),
                correct: result.pretest_by_type?.[type] ?? 0,
              }))}
              outerRadius="70%"
            >
              <PolarGrid stroke="var(--border)" />
              <PolarAngleAxis
                dataKey="type"
                tick={{ fontSize: 12, fill: "var(--foreground)" }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 4]}
                tickCount={5}
                tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
              />
              <Radar
                name="答對題數"
                dataKey="correct"
                stroke="var(--primary)"
                fill="var(--primary)"
                fillOpacity={0.3}
              />
            </RadarChart>
          </ResponsiveContainer>
          <ul className="grid gap-1 text-sm">
            {FRAUD_TYPES.map((type) => (
              <li key={type}>
                {fraudTypeLabel(type)}：{result.pretest_by_type?.[type] ?? 0}／4
                題
              </li>
            ))}
          </ul>
        </section>
      )}
      {/* 放棄或到期時可能根本沒做到話術題，這時不寫「沒有漏掉」 */}
      {(state.status === "completed" || result.missed_tactics.length > 0) && (
        <section className="rounded-2xl border bg-card p-4">
          <h2 className="font-bold">漏掉的話術</h2>
          {result.missed_tactics.length ? (
            <ul className="mt-2 list-inside list-disc text-sm">
              {result.missed_tactics.map((label) => (
                <li key={label}>{label}</li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-muted-foreground">
              這次沒有漏掉的話術。
            </p>
          )}
        </section>
      )}
      {result.badges.length > 0 && <ExamBadges badges={result.badges} />}
      {(result.reward.cash ?? 0) + (result.reward.xp ?? 0) > 0 && (
        <p className="text-sm">
          獲得 {result.reward.cash ?? 0} 遊戲幣、{result.reward.xp ?? 0} 經驗。
        </p>
      )}
      {!result.passed && (
        // 首頁的補考卡列出滑卡、訊息判讀、情境對抗三個入口，門檻三種都要練
        <Link
          to="/"
          className="block rounded-xl bg-primary p-3 text-center font-bold text-primary-foreground"
        >
          先去練{fraudTypeLabel(result.fraud_type)}
        </Link>
      )}
      <Link to="/exam" className="block text-center text-primary underline">
        {result.passed ? "回檢測頁" : "回檢測頁查看補考進度"}
      </Link>
    </div>
  )
}
