import type { ScenarioInboxItem } from "@/client"
import { FRAUD_TYPE_LABELS, OUTCOME_BADGES } from "./labels"

interface InboxListProps {
  items: ScenarioInboxItem[]
  onOpen: (item: ScenarioInboxItem) => void
}

/** 情境收件匣:GTA 式聯絡人清單(中性名字 + 類型標籤 + 最新訊息預覽) */
export function InboxList({ items, onOpen }: InboxListProps) {
  return (
    <ul className="divide-y divide-border">
      {items.map((item) => {
        const badge = item.outcome ? OUTCOME_BADGES[item.outcome] : null
        return (
          <li key={item.id}>
            <button
              type="button"
              onClick={() => onOpen(item)}
              data-testid={`inbox-row-${item.id}`}
              className="flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-muted/50"
            >
              <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-muted text-xl">
                {item.avatar}
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex items-center gap-1.5 text-sm font-bold">
                  {item.display_name}
                  <span className="rounded-md bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
                    {FRAUD_TYPE_LABELS[item.fraud_type] ?? item.fraud_type}
                  </span>
                </span>
                <span className="mt-0.5 block truncate text-xs text-muted-foreground">
                  {item.preview}
                </span>
              </span>
              <span className="flex shrink-0 flex-col items-end gap-1.5 pt-1">
                {item.unread && (
                  <span
                    data-testid={`unread-${item.id}`}
                    className="size-2.5 rounded-full bg-green-500"
                  />
                )}
                {badge && (
                  <span
                    className={`text-[10px] font-bold ${
                      badge.tone === "win" ? "text-green-600" : "text-red-600"
                    }`}
                  >
                    {badge.label}
                  </span>
                )}
              </span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
