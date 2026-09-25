import type { ScenarioInboxItem } from "@/client"
import { fraudTypeLabel } from "@/lib/fraudTypes"
import { OutcomeBadge } from "./OutcomeBadge"
import { ScenarioAvatar } from "./ScenarioAvatar"

interface InboxListProps {
  items: ScenarioInboxItem[]
  onOpen: (item: ScenarioInboxItem) => void
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
            data-testid={`inbox-row-${item.id}`}
            className="flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-muted/50"
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
