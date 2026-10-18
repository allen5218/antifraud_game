import type { ScenarioInboxItem } from "@/client"
import { fraudTypeLabel } from "@/lib/fraudTypes"
import { OUTCOME_BADGES } from "./labels"
import { OutcomeBadge } from "./OutcomeBadge"
import { ScenarioAvatar } from "./ScenarioAvatar"

interface InboxListProps {
  items: ScenarioInboxItem[]
  onOpen: (item: ScenarioInboxItem) => void
}

/** 螢幕閱讀器念的按鈕名稱：誰、哪一類、未讀或結果、最新訊息 */
function rowLabel(item: ScenarioInboxItem): string {
  return [
    item.display_name,
    fraudTypeLabel(item.fraud_type),
    item.unread ? "未讀" : null,
    item.outcome ? OUTCOME_BADGES[item.outcome]?.label : null,
    item.preview,
  ]
    .filter(Boolean)
    .join("，")
}

/** 情境收件匣：聯絡人清單（名字、類型標籤、最新訊息預覽） */
export function InboxList({ items, onOpen }: InboxListProps) {
  return (
    <ul className="divide-y divide-border">
      {items.map((item) => (
        <li key={item.id}>
          <button
            type="button"
            onClick={() => onOpen(item)}
            aria-label={rowLabel(item)}
            data-testid={`inbox-row-${item.id}`}
            className="flex w-full items-start gap-3 bg-card px-4 py-3 text-left hover:bg-muted/50"
          >
            <ScenarioAvatar avatar={item.avatar} />
            <span className="min-w-0 flex-1">
              <span className="flex items-center gap-1.5 text-sm font-bold">
                {item.display_name}
                <span className="rounded-md bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
                  {fraudTypeLabel(item.fraud_type)}
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
                  role="img"
                  aria-label="未讀"
                  className="size-2.5 rounded-full bg-primary"
                />
              )}
              {item.outcome && (
                <OutcomeBadge outcome={item.outcome} className="text-[10px]" />
              )}
            </span>
          </button>
        </li>
      ))}
    </ul>
  )
}
