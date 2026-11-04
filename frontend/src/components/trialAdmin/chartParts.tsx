/** 試測分析共用的卡片、數字卡與圖表樣式 */

export const AXIS_TICK = { fontSize: 11, fill: "var(--muted-foreground)" }
export const TOOLTIP_STYLE = {
  background: "var(--popover)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  color: "var(--popover-foreground)",
  fontSize: 12,
}
// 提示框的字用文字色，不用數列的顏色
export const TOOLTIP_ITEM = { color: "var(--popover-foreground)" }

export function pct(part: number, whole: number): string {
  return whole ? `${Math.round((part / whole) * 100)}%` : "–"
}

export function num(value: number | null | undefined, digits = 1): string {
  return value == null ? "–" : value.toFixed(digits).replace(/\.0+$/, "")
}

export function Card({
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

export function Tiles({ items }: { items: [string, string][] }) {
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
