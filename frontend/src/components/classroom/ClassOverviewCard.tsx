import type { ClassOverview } from "@/client"
import { fraudTypeLabel } from "@/lib/fraudTypes"
import { percent, weakestSentence } from "./format"

/** 全班五類答對率；最弱那一類標出來並寫成一句話 */
export function ClassOverviewCard({ data }: { data: ClassOverview }) {
  const sentence = weakestSentence(data.weakest, data.type_accuracy)
  return (
    <section className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4">
      <h2 className="text-lg font-bold">全班哪一類最弱</h2>
      {sentence ? (
        <>
          <p className="text-base font-bold text-warning">{sentence}</p>
          <p className="text-xs text-muted-foreground">
            依 {data.accuracy_n} 位學生最近一次的前測
          </p>
          <ul className="flex flex-col gap-2">
            {data.type_accuracy.map((t) => {
              const weak = data.weakest.includes(t.fraud_type)
              return (
                <li
                  key={t.fraud_type}
                  className="grid grid-cols-[5rem_1fr_4.5rem] items-center gap-2 text-sm"
                >
                  <span className={weak ? "font-bold" : undefined}>
                    {fraudTypeLabel(t.fraud_type)}
                  </span>
                  <span className="h-3 overflow-hidden rounded-full bg-surface-2">
                    <span
                      className={`block h-full rounded-full ${weak ? "bg-warning" : "bg-chart-after"}`}
                      style={{
                        width: `${Math.round((t.accuracy ?? 0) * 100)}%`,
                      }}
                    />
                  </span>
                  <span className="text-right text-muted-foreground">
                    {percent(t.accuracy)}
                  </span>
                </li>
              )
            })}
          </ul>
        </>
      ) : (
        <p className="text-muted-foreground">
          還沒有學生做過前測。學生考完綜合檢測（第一關就是前測）或做完入門前測，這裡就會出現。
        </p>
      )}
    </section>
  )
}
