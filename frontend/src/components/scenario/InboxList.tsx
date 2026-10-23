import { Search } from "lucide-react"
import { useState } from "react"
import type { ScenarioInboxItem } from "@/client"
import { fraudTypeLabel } from "@/lib/fraudTypes"
import { OUTCOME_BADGES } from "./labels"
import { chatDay, chatTime } from "./MessageList"
import { OutcomeBadge } from "./OutcomeBadge"
import { ScenarioAvatar } from "./ScenarioAvatar"

interface InboxListProps {
  items: ScenarioInboxItem[]
  onOpen: (item: ScenarioInboxItem) => void
}

/** 聊天列表右上的時間：今天寫幾點，昨天寫「昨天」，更早寫日期 */
export function listTime(at: string | null | undefined, now = new Date()) {
  if (!at) return ""
  const day = chatDay(at, now)
  if (day === "今天") return chatTime(at)
  if (day === "昨天") return day
  const date = new Date(at)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

function unreadCount(item: ScenarioInboxItem): number {
  return item.unread ? item.unread_count || 1 : 0
}

/** 螢幕閱讀器念的按鈕名稱：誰、哪一類、未讀或結果、最新訊息 */
function rowLabel(item: ScenarioInboxItem): string {
  const unread = unreadCount(item)
  return [
    item.display_name,
    fraudTypeLabel(item.fraud_type),
    unread ? `未讀 ${unread} 則` : null,
    item.outcome ? OUTCOME_BADGES[item.outcome]?.label : null,
    item.preview,
  ]
    .filter(Boolean)
    .join("，")
}

/** 情境收件匣：像手機聊天軟體的聊天列表（頭貼、名字、最新訊息、時間、未讀數） */
export function InboxList({ items, onOpen }: InboxListProps) {
  const [query, setQuery] = useState("")
  const keyword = query.trim()
  const shown = keyword
    ? items.filter(
        (item) =>
          item.display_name.includes(keyword) ||
          item.preview.includes(keyword) ||
          fraudTypeLabel(item.fraud_type).includes(keyword),
      )
    : items
  return (
    <div className="flex flex-col">
      <label className="mx-4 mb-2 flex items-center gap-2 rounded-full bg-muted px-3 py-2 text-sm text-muted-foreground">
        <Search aria-hidden className="size-4 shrink-0" />
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="搜尋聊天"
          aria-label="搜尋聊天"
          className="min-w-0 flex-1 bg-transparent text-foreground outline-none placeholder:text-muted-foreground"
        />
      </label>
      {shown.length === 0 && (
        <p className="py-8 text-center text-xs text-muted-foreground">
          找不到符合的聊天
        </p>
      )}
      <ul>
        {shown.map((item) => {
          const unread = unreadCount(item)
          return (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => onOpen(item)}
                aria-label={rowLabel(item)}
                data-testid={`inbox-row-${item.id}`}
                className="flex w-full items-center gap-3 px-4 py-2.5 text-left hover:bg-muted/50 active:bg-muted"
              >
                <ScenarioAvatar avatar={item.avatar} className="size-12" />
                <span className="min-w-0 flex-1">
                  <span className="flex items-baseline gap-2">
                    <span className="truncate text-[15px] font-bold">
                      {item.display_name}
                    </span>
                    <span className="shrink-0 text-[10px] text-muted-foreground">
                      {fraudTypeLabel(item.fraud_type)}
                    </span>
                    <time
                      dateTime={item.last_at ?? undefined}
                      className="ml-auto shrink-0 text-[11px] text-muted-foreground"
                    >
                      {listTime(item.last_at)}
                    </time>
                  </span>
                  <span className="mt-0.5 flex items-center gap-2">
                    <span
                      className={`min-w-0 flex-1 truncate text-[13px] ${
                        unread ? "text-foreground" : "text-muted-foreground"
                      }`}
                    >
                      {item.preview}
                    </span>
                    {unread > 0 && (
                      <span
                        data-testid={`unread-${item.id}`}
                        aria-hidden
                        className="flex h-5 min-w-5 shrink-0 items-center justify-center rounded-full bg-primary px-1.5 text-[11px] font-bold text-primary-foreground"
                      >
                        {unread}
                      </span>
                    )}
                    {item.outcome && (
                      <OutcomeBadge
                        outcome={item.outcome}
                        className="shrink-0 text-[10px]"
                      />
                    )}
                  </span>
                </span>
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
