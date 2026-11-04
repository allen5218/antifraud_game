import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import type {
  CurvePoint,
  EffectAnalytics,
  PairedChange,
  SurveyAnalytics,
} from "@/client"
import { fraudTypeLabel } from "@/lib/fraudTypes"
import {
  AXIS_TICK,
  Card,
  num,
  pct,
  Tiles,
  TOOLTIP_ITEM,
  TOOLTIP_STYLE,
} from "./chartParts"

const BEFORE = "var(--chart-before)"
const AFTER = "var(--chart-after)"
const FEW = 5
const SELF_RATED = ["distinguish", "verify_channel", "pause_confidence"]

/** 有人數的卡：沒有資料就不畫，人數少就提醒 */
function EffectCard({
  title,
  note,
  n,
  children,
}: {
  title: string
  note: string
  n: number
  children: React.ReactNode
}) {
  return (
    <Card title={title} note={note}>
      {n === 0 ? (
        <p className="text-sm text-muted-foreground">還沒有資料</p>
      ) : (
        <>
          {n < FEW && (
            <p className="text-xs font-medium text-warning">
              人數少，只供參考。
            </p>
          )}
          {children}
        </>
      )}
    </Card>
  )
}

/** 「平均 25% → 80%，8 人裡 6 人進步」；下一行寫一樣與退步 */
function Summary({
  change,
  unit,
  better = "進步",
  same = "一樣",
  worse = "退步",
}: {
  change: PairedChange
  unit: string
  better?: string
  same?: string
  worse?: string
}) {
  return (
    <div className="text-sm">
      <p className="font-bold">
        {`平均 ${num(change.before_mean)}${unit} → ${num(change.after_mean)}${unit}，${change.n} 人裡 ${change.improved} 人${better}`}
      </p>
      <p className="text-xs text-muted-foreground">
        {same} {change.same} 人・{worse} {change.worse} 人
      </p>
    </div>
  )
}

function Legend2({ before, after }: { before: string; after: string }) {
  return (
    <p className="flex flex-wrap gap-3 text-xs text-muted-foreground">
      <span className="flex items-center gap-1">
        <span className="size-2.5 rounded-sm" style={{ background: BEFORE }} />
        {before}
      </span>
      <span className="flex items-center gap-1">
        <span className="size-2.5 rounded-sm" style={{ background: AFTER }} />
        {after}
      </span>
    </p>
  )
}

function Bar({
  value,
  max,
  color,
}: {
  value: number | null
  max: number
  color: string
}) {
  return (
    <span className="h-2.5 rounded-r-[4px] bg-surface-2">
      <span
        className="block h-2.5 rounded-r-[4px]"
        style={{
          width: `${value == null ? 0 : (value / max) * 100}%`,
          background: color,
        }}
      />
    </span>
  )
}

type PairRow = {
  key: string
  label: string
  before: number | null
  after: number | null
  hint?: string
}

/** 一列一個項目，上面一條是前、下面一條是後，數字寫在旁邊（不靠顏色） */
function PairRows({
  rows,
  unit,
  max,
}: {
  rows: PairRow[]
  unit: string
  max?: number
}) {
  const top =
    max ?? Math.max(1, ...rows.flatMap((r) => [r.before ?? 0, r.after ?? 0]))
  const text = (v: number | null) => (v == null ? "–" : `${num(v)}${unit}`)
  return (
    <ul className="flex flex-col gap-2 text-sm">
      {rows.map((r) => (
        <li
          key={r.key}
          className="grid grid-cols-[minmax(4.5rem,8rem)_1fr_auto] items-center gap-x-2 gap-y-1"
          title={`${r.label}：${text(r.before)} → ${text(r.after)}${r.hint ? `（${r.hint}）` : ""}`}
        >
          <span className="row-span-2 truncate">{r.label}</span>
          <Bar value={r.before} max={top} color={BEFORE} />
          <span className="w-14 text-right text-xs tabular-nums text-muted-foreground">
            {text(r.before)}
          </span>
          <Bar value={r.after} max={top} color={AFTER} />
          <span className="w-14 text-right text-xs tabular-nums">
            {text(r.after)}
          </span>
        </li>
      ))}
    </ul>
  )
}

/** 單一數列：一列一條 */
function SingleRows({
  rows,
  firstIsBefore = false,
}: {
  rows: { key: string; label: string; value: number | null; hint: string }[]
  firstIsBefore?: boolean
}) {
  return (
    <ul className="flex flex-col gap-1.5 text-sm">
      {rows.map((r, i) => (
        <li
          key={r.key}
          className="grid grid-cols-[minmax(4.5rem,8rem)_1fr_auto] items-center gap-2"
          title={`${r.label}：${r.value == null ? "沒有資料" : `${num(r.value)}%`}（${r.hint}）`}
        >
          <span className="truncate">{r.label}</span>
          <Bar
            value={r.value}
            max={100}
            color={firstIsBefore && i === 0 ? BEFORE : AFTER}
          />
          <span className="w-14 text-right text-xs tabular-nums">
            {r.value == null ? "–" : `${num(r.value)}%`}
          </span>
        </li>
      ))}
    </ul>
  )
}

function Curve({ points }: { points: CurvePoint[] }) {
  return (
    <>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={points} margin={{ top: 12, right: 8, left: -24 }}>
          <CartesianGrid vertical={false} stroke="var(--border)" />
          <XAxis dataKey="label" tick={AXIS_TICK} interval={0} />
          <YAxis domain={[0, 100]} unit="%" tick={AXIS_TICK} />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            itemStyle={TOOLTIP_ITEM}
            labelFormatter={(label, items) => {
              const p = items?.[0]?.payload as CurvePoint | undefined
              return p
                ? `第 ${label} 題（${p.people} 人、${p.items} 題）`
                : label
            }}
            formatter={(value, name) => [
              value == null ? "沒有資料" : `${value}%`,
              name,
            ]}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line
            dataKey="accuracy"
            name="答對率"
            stroke={AFTER}
            strokeWidth={2}
            dot={{ r: 4, fill: AFTER, stroke: "var(--card)", strokeWidth: 2 }}
            isAnimationActive={false}
          />
          <Line
            dataKey="missed_rate"
            name="漏掉話術的題目比例"
            stroke={BEFORE}
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={{ r: 4, fill: BEFORE, stroke: "var(--card)", strokeWidth: 2 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
      <ul className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
        {points.map((p) => (
          <li key={p.label}>
            第 {p.label} 題：{p.people} 人
          </li>
        ))}
      </ul>
    </>
  )
}

/** 成效：前測和之後的作答比一比（給評審看的那幾張） */
export function EffectSection({
  effect,
  survey,
}: {
  effect: EffectAnalytics
  survey: SurveyAnalytics
}) {
  const { exam, entry, repeat, practice, volume } = effect
  const practiced = practice.curve[0]?.people ?? 0
  const modeN = Math.max(0, ...practice.modes.map((m) => m.change.n))
  const tagMax = Math.max(
    1,
    ...practice.tags.flatMap((t) => [t.first_half, t.second_half]),
  )
  const selfRated = SELF_RATED.flatMap((id) => {
    const item = survey.likert.find((i) => i.id === id)
    if (!item) return []
    const agree = (item.counts[3] ?? 0) + (item.counts[4] ?? 0)
    return [
      {
        key: id,
        label: item.question,
        value: item.n ? Math.round((agree / item.n) * 1000) / 10 : null,
        hint: `${item.n} 人裡 ${agree} 人選同意或非常同意`,
      },
    ]
  })
  const conf = survey.confidence
  return (
    <div className="grid gap-3 lg:grid-cols-2">
      <EffectCard
        title="檢測：前測關到後三關"
        note="每人第一次考完的綜合檢測。前測關挑出最弱的一類，後面三關只考這一類。最弱的一類本來就是前測挑出來的，後面的題型也不同，所以分數回升不全是練習的效果。"
        n={exam.change.n}
      >
        <SingleRows
          firstIsBefore
          rows={exam.stages.map((s) => ({
            key: s.key,
            label: s.label,
            value: s.accuracy,
            hint: `${s.people} 人、${s.items} 題`,
          }))}
        />
        <Summary change={exam.change} unit="%" />
      </EffectCard>

      <EffectCard
        title="入門前測到綜合檢測的前測關"
        note={`兩份同一個題庫、同樣的抽法（五類各 4 題）。只算先做入門前測、之後考綜合檢測的人；兩次中間有練習的 ${entry.practiced_between} 人。`}
        n={entry.total.n}
      >
        <Summary change={entry.total} unit="%" />
        <Legend2 before="入門前測" after="綜合檢測的前測關" />
        <PairRows
          rows={entry.by_type.map((t) => ({
            key: t.fraud_type,
            label: fraudTypeLabel(t.fraud_type),
            before: t.before,
            after: t.after,
            hint: `${t.people} 人`,
          }))}
          unit="%"
          max={100}
        />
      </EffectCard>

      <EffectCard
        title="考兩次以上的人"
        note="第一次和最近一次正常交卷的綜合檢測。"
        n={repeat.people + repeat.failed_first}
      >
        {repeat.people > 0 && (
          <>
            <p className="text-xs text-muted-foreground">
              前測關答對題數（20 題）
            </p>
            <Summary change={repeat.pretest} unit=" 題" />
            <p className="text-xs text-muted-foreground">檢測分數</p>
            <Summary change={repeat.score} unit=" 分" />
          </>
        )}
        <p className="text-sm">
          第一次沒過 {repeat.failed_first} 人，其中再考 {repeat.retook}{" "}
          人、之後通過 {repeat.retake_passed} 人。
        </p>
      </EffectCard>

      <EffectCard
        title="日常練習：起點到之後"
        note="起點是入門前測，沒做入門前測的用綜合檢測的前測關；之後是滑卡、訊息判讀、情境對抗的練習。每類把所有人的題目合起來算。"
        n={practiced}
      >
        <Legend2 before="起點" after="之後的練習" />
        <PairRows
          rows={practice.by_type.map((t) => ({
            key: t.fraud_type,
            label: fraudTypeLabel(t.fraud_type),
            before: t.before,
            after: t.after,
            hint: `${t.people} 人`,
          }))}
          unit="%"
          max={100}
        />
      </EffectCard>

      <EffectCard
        title="練習越多，答對率怎麼變"
        note="每人的練習依時間排，每 10 題算一次。越後面的點練到的人越少，滑過看人數。"
        n={practiced}
      >
        <Curve points={practice.curve} />
      </EffectCard>

      <EffectCard
        title="漏掉的話術：前半到後半"
        note="每人的練習切成前後兩半，答錯時漏掉的話術各幾次。次數變少代表比較認得出來。"
        n={practiced}
      >
        <Legend2 before="前半" after="後半" />
        <PairRows
          rows={practice.tags.map((t) => ({
            key: t.tag,
            label: t.label,
            before: t.first_half,
            after: t.second_half,
          }))}
          unit=" 次"
          max={tagMax}
        />
      </EffectCard>

      <EffectCard
        title="三種練習：前半到後半"
        note="每人每種練習至少 4 題才算，比較前半和後半的答對率。"
        n={modeN}
      >
        <Legend2 before="前半" after="後半" />
        <PairRows
          rows={practice.modes.map((m) => ({
            key: m.mode,
            label: `${m.label}（${m.change.n} 人）`,
            before: m.change.before_mean,
            after: m.change.after_mean,
            hint: `${m.change.improved} 人進步`,
          }))}
          unit="%"
          max={100}
        />
      </EffectCard>

      <EffectCard
        title="練習量"
        note="考完綜合檢測之後，自己回來練習的情形。"
        n={volume.exam_people}
      >
        <Tiles
          items={[
            ["考完檢測", `${volume.exam_people} 人`],
            [
              "之後還有練習",
              `${volume.practiced_people} 人（${pct(volume.practiced_people, volume.exam_people)}）`,
            ],
            ["每人題數中位數", num(volume.median_answers)],
            ["練習天數中位數", num(volume.median_days)],
          ]}
        />
        <p className="text-sm">情境對抗練了 {volume.scenario_rounds} 場。</p>
      </EffectCard>

      <EffectCard
        title="問卷自評"
        note="受試者交問卷時自己評的。信心是 1 非常沒信心到 5 非常有信心。"
        n={survey.responses}
      >
        <p className="text-xs text-muted-foreground">辨識詐騙的信心</p>
        <Summary
          change={conf}
          unit=" 分"
          better="提高"
          same="不變"
          worse="降低"
        />
        <p className="text-xs text-muted-foreground">選同意或非常同意的比例</p>
        <SingleRows rows={selfRated} />
      </EffectCard>
    </div>
  )
}
