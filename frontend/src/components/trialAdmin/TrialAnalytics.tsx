import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import {
  AdminCohortsService,
  type TrialAnalytics as Analytics,
  type CohortPublic,
  type HistogramBin,
  type LikertItem,
} from "@/client"
import { Button } from "@/components/ui/button"
import { fraudTypeLabel } from "@/lib/fraudTypes"

const AXIS_TICK = { fontSize: 11, fill: "var(--muted-foreground)" }
const TOOLTIP_STYLE = {
  background: "var(--popover)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  color: "var(--popover-foreground)",
  fontSize: 12,
}
// 提示框的字用文字色，不用數列的顏色
const TOOLTIP_ITEM = { color: "var(--popover-foreground)" }
const LIKERT_COLORS = [1, 2, 3, 4, 5].map((n) => `var(--likert-${n})`)
// 直方圖裡「不算數」的區間（沒過關、太快）用灰色
const BELOW_COLOR = "var(--likert-3)"

function pct(part: number, whole: number): string {
  return whole ? `${Math.round((part / whole) * 100)}%` : "–"
}

function num(value: number | null | undefined, digits = 1): string {
  return value == null ? "–" : value.toFixed(digits).replace(/\.0+$/, "")
}

function Card({
  title,
  note,
  children,
}: {
  title: string
  note?: string
  children: React.ReactNode
}) {
  return (
    <section className="flex min-w-0 flex-col gap-2 rounded-xl border border-border bg-card p-4">
      <h4 className="font-bold">{title}</h4>
      {note && <p className="text-xs text-muted-foreground">{note}</p>}
      {children}
    </section>
  )
}

function Tiles({ items }: { items: [string, string][] }) {
  return (
    <dl className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      {items.map(([label, value]) => (
        <div key={label} className="rounded-lg bg-surface-2 p-2 text-center">
          <dt className="text-[11px] text-muted-foreground">{label}</dt>
          <dd className="text-lg font-bold">{value}</dd>
        </div>
      ))}
    </dl>
  )
}

/** 單一數列的橫條：長度就是人數，旁邊寫數字（不靠顏色） */
function HBars({
  rows,
  total,
}: {
  rows: { label: string; count: number }[]
  total: number
}) {
  const max = Math.max(1, ...rows.map((r) => r.count))
  return (
    <ul className="flex flex-col gap-1.5 text-sm">
      {rows.map((r) => (
        <li
          key={r.label}
          className="grid grid-cols-[minmax(5rem,9rem)_1fr_auto] items-center gap-2"
          title={`${r.label}：${r.count} 人（${pct(r.count, total)}）`}
        >
          <span className="truncate">{r.label}</span>
          <span className="h-3 rounded-r-[4px] bg-surface-2">
            <span
              className="block h-3 rounded-r-[4px] bg-primary"
              style={{ width: `${(r.count / max) * 100}%` }}
            />
          </span>
          <span className="w-16 text-right tabular-nums text-muted-foreground">
            {r.count}・{pct(r.count, total)}
          </span>
        </li>
      ))}
    </ul>
  )
}

function Histogram({
  bins,
  passLabel,
  belowLabel,
  unit,
}: {
  bins: HistogramBin[]
  passLabel: string
  belowLabel: string
  unit: string
}) {
  return (
    <>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={bins} margin={{ top: 16, right: 4, left: -24 }}>
          <CartesianGrid vertical={false} stroke="var(--border)" />
          {/* 手機上區間寫不下，軸上只寫起點，完整區間在提示框 */}
          <XAxis
            dataKey="label"
            tick={AXIS_TICK}
            interval={0}
            tickFormatter={(label: string) =>
              label.endsWith("+") ? label : label.split("–")[0]
            }
          />
          <YAxis allowDecimals={false} tick={AXIS_TICK} />
          <Tooltip
            cursor={{ fill: "var(--surface-2)" }}
            contentStyle={TOOLTIP_STYLE}
            itemStyle={TOOLTIP_ITEM}
            formatter={(value) => [`${value} 人`, "人數"]}
            labelFormatter={(label) => `${label} ${unit}`}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={36}>
            {bins.map((b) => (
              <Cell
                key={b.label}
                fill={b.below ? BELOW_COLOR : "var(--primary)"}
              />
            ))}
            <LabelList
              dataKey="count"
              position="top"
              style={{ fontSize: 11, fill: "var(--foreground)" }}
              formatter={(v) => (Number(v) > 0 ? v : "")}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="flex flex-wrap gap-3 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <span className="size-2.5 rounded-sm bg-primary" />
          {passLabel}
        </span>
        <span className="flex items-center gap-1">
          <span
            className="size-2.5 rounded-sm"
            style={{ background: BELOW_COLOR }}
          />
          {belowLabel}
        </span>
      </p>
    </>
  )
}

function TrialSection({ data }: { data: Analytics }) {
  const joined = data.member_count
  return (
    <div className="grid gap-3 lg:grid-cols-2">
      <Card title="試測流程" note="每一步做完的人數，百分比以加入人數為準。">
        <HBars
          rows={data.funnel.map((s) => ({ label: s.label, count: s.count }))}
          total={joined}
        />
      </Card>
      <Card
        title="五類答對率：綜合檢測的前測關"
        note="每人第一次考完的綜合檢測，第一關 20 題前測，把同一類的題目合起來算答對率；滑過看題數。"
      >
        <ResponsiveContainer width="100%" height={240}>
          <BarChart
            data={data.type_accuracy.map((t) => ({
              type: fraudTypeLabel(t.fraud_type),
              accuracy:
                t.accuracy == null ? null : Math.round(t.accuracy * 100),
              n: t.n,
            }))}
            margin={{ top: 16, right: 4, left: -24 }}
          >
            <CartesianGrid vertical={false} stroke="var(--border)" />
            <XAxis dataKey="type" tick={AXIS_TICK} interval={0} />
            <YAxis domain={[0, 100]} unit="%" tick={AXIS_TICK} />
            <Tooltip
              cursor={{ fill: "var(--surface-2)" }}
              contentStyle={TOOLTIP_STYLE}
              itemStyle={TOOLTIP_ITEM}
              formatter={(value, name, item) => [
                value == null
                  ? "沒有資料"
                  : `${value}%（${item.payload.n} 題）`,
                name,
              ]}
            />
            <Bar
              dataKey="accuracy"
              name="答對率"
              fill="var(--chart-after)"
              radius={[4, 4, 0, 0]}
              maxBarSize={36}
            />
          </BarChart>
        </ResponsiveContainer>
      </Card>
      <Card
        title="檢測分數"
        note={`每人最好的一次正常交卷。${data.scores.n} 人交卷，${data.scores.passed} 人過關（${pct(data.scores.passed, data.scores.n)}），平均 ${num(data.scores.mean)} 分。`}
      >
        <Histogram
          bins={data.scores.bins}
          passLabel="70 分以上（過關）"
          belowLabel="沒過"
          unit="分"
        />
      </Card>
      {data.timings.map((t) => (
        <Card
          key={t.key}
          title={`用時：${t.label}`}
          note={`${t.n} 人有紀錄，中位數 ${t.median_seconds == null ? "–" : `${Math.round(t.median_seconds)} 秒`}；少於 ${t.threshold_seconds} 秒的 ${t.below} 人不能領錢。`}
        >
          <Histogram
            bins={t.bins}
            passLabel="時間夠"
            belowLabel="太快（不能領錢）"
            unit={t.key === "exam" ? "分鐘" : "秒"}
          />
        </Card>
      ))}
    </div>
  )
}

/** 五點量表：一題一條 100% 堆疊橫條，左邊是 1、右邊是 5；平均與人數寫在旁邊 */
function LikertRows({ items }: { items: LikertItem[] }) {
  return (
    <ul className="flex flex-col gap-3">
      {items.map((item) => (
        <li key={item.id} className="flex flex-col gap-1 text-sm">
          <div className="flex items-baseline gap-2">
            <span className="flex-1">{item.question}</span>
            <span className="shrink-0 tabular-nums text-muted-foreground">
              平均 {num(item.mean, 2)}・{item.n} 人
            </span>
          </div>
          <div className="flex h-4 gap-[2px] overflow-hidden rounded-[4px] bg-surface-2">
            {item.counts.map((count, i) =>
              count > 0 ? (
                <span
                  key={item.labels[i]}
                  title={`${i + 1} ${item.labels[i]}：${count} 人（${pct(count, item.n)}）`}
                  className="h-full"
                  style={{
                    width: `${(count / item.n) * 100}%`,
                    background: LIKERT_COLORS[i],
                  }}
                />
              ) : null,
            )}
          </div>
        </li>
      ))}
    </ul>
  )
}

function LikertTable({ items }: { items: LikertItem[] }) {
  return (
    <details className="text-sm">
      <summary className="cursor-pointer text-primary">看數字</summary>
      <div className="mt-2 overflow-x-auto">
        <table className="w-full text-left tabular-nums">
          <thead>
            <tr className="border-b border-border">
              <th className="p-1">題目</th>
              {[1, 2, 3, 4, 5].map((n) => (
                <th key={n} className="p-1 text-right">
                  {n}
                </th>
              ))}
              <th className="p-1 text-right">平均</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-b border-border">
                <td className="p-1">{item.question}</td>
                {item.counts.map((c, i) => (
                  <td key={item.labels[i]} className="p-1 text-right">
                    {c}
                  </td>
                ))}
                <td className="p-1 text-right">{num(item.mean, 2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  )
}

function SurveySection({ data }: { data: Analytics }) {
  const survey = data.survey
  const sections = [...new Set(survey.likert.map((i) => i.section))]
  const agreeLabels =
    survey.likert.find((i) => i.id !== "confidence_before")?.labels ?? []
  const conf = survey.confidence
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-muted-foreground">
        交了問卷的 {survey.responses}{" "}
        人全部列入分析，注意力題答錯的也算；注意力題本身不列。
      </p>
      {survey.responses === 0 ? (
        <p className="text-muted-foreground">還沒有問卷可以分析。</p>
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          <Card
            title="辨識詐騙的信心：玩之前 vs 玩完後"
            note="同一份問卷的兩題相減；1 非常沒信心、5 非常有信心。"
          >
            <Tiles
              items={[
                ["玩之前平均", num(conf.before_mean, 2)],
                ["玩完後平均", num(conf.after_mean, 2)],
                [
                  "平均提高",
                  conf.diff_mean == null
                    ? "–"
                    : `${conf.diff_mean > 0 ? "+" : ""}${num(conf.diff_mean, 2)}`,
                ],
                ["提高的人", `${conf.improved}／${conf.n}`],
              ]}
            />
            <p className="text-sm">
              提高 {conf.improved} 人・不變 {conf.same} 人・降低 {conf.worse} 人
            </p>
          </Card>
          <Card title="五點量表" note="每條由左到右是 1 到 5，滑過看人數。">
            <p className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
              {agreeLabels.map((label, i) => (
                <span key={label} className="flex items-center gap-1">
                  <span
                    className="size-2.5 rounded-sm"
                    style={{ background: LIKERT_COLORS[i] }}
                  />
                  {i + 1} {label}
                </span>
              ))}
            </p>
            <p className="text-xs text-muted-foreground">
              信心兩題的 1～5 是「非常沒信心」到「非常有信心」。
            </p>
          </Card>
          {sections.map((section) => {
            const items = survey.likert.filter((i) => i.section === section)
            return (
              <Card key={section} title={section}>
                <LikertRows items={items} />
                <LikertTable items={items} />
              </Card>
            )
          })}
          {survey.choices.map((choice) => (
            <Card
              key={choice.id}
              title={choice.question}
              note={`${choice.n} 人回答${choice.multi ? "（可複選，百分比以回答人數為準）" : ""}`}
            >
              <HBars
                rows={choice.options.map((o) => ({
                  label: o.label,
                  count: o.count,
                }))}
                total={choice.n}
              />
            </Card>
          ))}
          {survey.texts.map((text) => (
            <Card
              key={text.id}
              title={text.question}
              note={`${text.answers.length} 則`}
            >
              {text.answers.length === 0 ? (
                <p className="text-sm text-muted-foreground">沒有人寫。</p>
              ) : (
                <ul className="flex max-h-72 flex-col gap-1 overflow-y-auto text-sm">
                  {text.answers.map((a, i) => (
                    <li
                      key={`${a.participant_code}-${i}`}
                      className="rounded-lg bg-surface-2 p-2"
                    >
                      <span className="mr-2 text-xs text-muted-foreground">
                        {a.participant_code}
                      </span>
                      <span className="whitespace-pre-wrap">{a.text}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

/** 試測數據與問卷分析：可以看單一梯次或全部梯次合計 */
export function TrialAnalytics({ cohorts }: { cohorts: CohortPublic[] }) {
  const [scope, setScope] = useState("")
  const analytics = useQuery({
    queryKey: ["admin", "cohorts", "analytics", scope],
    queryFn: () =>
      AdminCohortsService.analytics({ cohortId: scope || undefined }),
  })
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label
            htmlFor="analytics-scope"
            className="mb-1 block text-sm font-medium"
          >
            看哪個梯次
          </label>
          <select
            id="analytics-scope"
            value={scope}
            onChange={(event) => setScope(event.target.value)}
            className="h-9 rounded-md border border-input bg-background px-2 text-sm"
          >
            <option value="">全部梯次合計</option>
            {cohorts.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        <Button variant="outline" onClick={() => analytics.refetch()}>
          更新
        </Button>
      </div>
      {analytics.isPending && <output>正在計算…</output>}
      {analytics.isError && (
        <p role="alert" className="text-scam">
          讀不到數據，請再更新一次。
        </p>
      )}
      {analytics.data && (
        <>
          <h3 className="text-lg font-bold">
            試測數據（{analytics.data.member_count} 人）
          </h3>
          <TrialSection data={analytics.data} />
          <h3 className="text-lg font-bold">問卷分析</h3>
          <SurveySection data={analytics.data} />
        </>
      )}
    </div>
  )
}
