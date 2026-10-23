import { type ReactNode, useEffect, useRef } from "react"
import { cn } from "@/lib/utils"
import { ScenarioAvatar } from "./ScenarioAvatar"

export type ChatEntry =
  | {
      role: "npc"
      messages: string[]
      decision_point: string | null
      at: string | null
    }
  | { role: "player"; text: string; at: string | null }

/** 後端 history 是寬鬆 dict;窄化成 ChatEntry。舊紀錄沒有時間(at) */
export function toChatEntries(
  history: Array<Record<string, unknown>>,
): ChatEntry[] {
  return history.map((e) => {
    const at = typeof e.at === "string" ? e.at : null
    return e.role === "npc"
      ? {
          role: "npc" as const,
          messages: (e.messages as string[]) ?? [],
          decision_point: (e.decision_point as string | null) ?? null,
          at,
        }
      : { role: "player" as const, text: (e.text as string) ?? "", at }
  })
}

/** 「下午3:21」：和手機聊天軟體一樣只顯示時間 */
export function chatTime(at: string | null): string {
  if (!at) return ""
  const date = new Date(at)
  if (Number.isNaN(date.getTime())) return ""
  return date.toLocaleTimeString("zh-TW", {
    hour: "numeric",
    minute: "2-digit",
  })
}

/** 日期分隔：今天、昨天，其他寫「10月21日（二）」 */
export function chatDay(at: string, now = new Date()): string {
  const date = new Date(at)
  const day = (d: Date) =>
    new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
  const diff = Math.round((day(now) - day(date)) / 86_400_000)
  if (diff === 0) return "今天"
  if (diff === 1) return "昨天"
  const weekday = "日一二三四五六"[date.getDay()]
  return `${date.getMonth() + 1}月${date.getDate()}日（${weekday}）`
}

// 對方的泡泡左上角、自己的泡泡右上角有一個小尾巴，像手機聊天軟體
const NPC_TAIL =
  "before:absolute before:top-0 before:-left-2 before:border-t-[10px] before:border-l-[10px] before:border-t-card before:border-l-transparent before:content-['']"
const PLAYER_TAIL =
  "before:absolute before:top-0 before:-right-2 before:border-t-[10px] before:border-r-[10px] before:border-t-primary before:border-r-transparent before:content-['']"

function Time({ at, read = false }: { at: string | null; read?: boolean }) {
  const time = chatTime(at)
  if (!time && !read) return null
  return (
    <span className="flex shrink-0 flex-col items-end text-[10px] leading-tight text-muted-foreground">
      {read && <span>已讀</span>}
      {time && <time dateTime={at ?? undefined}>{time}</time>}
    </span>
  )
}

interface MessageListProps {
  entries: ChatEntry[]
  typing: boolean
  /** 對方的頭貼代號與名字，放在對方每一段訊息旁邊 */
  avatar: string
  name: string
  /** 渲染在最後一則 npc 訊息之後(用於內嵌 ActionCard) */
  trailing?: ReactNode
}

export function MessageList({
  entries,
  typing,
  avatar,
  name,
  trailing,
}: MessageListProps) {
  // 和聊天軟體一樣停在最新訊息：打開時、有新訊息或「輸入中」出現時捲到最底。
  // 只捲外面那層對話框，不動整頁。
  const root = useRef<HTMLDivElement>(null)
  const size = entries.length + (typing ? 1 : 0) + (trailing ? 1 : 0)
  useEffect(() => {
    let box = root.current?.parentElement ?? null
    while (box && !/(auto|scroll)/.test(getComputedStyle(box).overflowY))
      box = box.parentElement
    if (box && size > 0) box.scrollTop = box.scrollHeight
  }, [size])
  // 玩家的訊息後面只要對方回過，就算「已讀」
  const lastNpc = entries.reduce(
    (found, entry, i) => (entry.role === "npc" ? i : found),
    -1,
  )
  const nodes: ReactNode[] = []
  let shownDay = ""
  entries.forEach((entry, i) => {
    const day = entry.at ? chatDay(entry.at) : ""
    if (day && day !== shownDay) {
      shownDay = day
      nodes.push(
        <div
          key={`day-${i}`}
          className="self-center rounded-full bg-foreground/10 px-3 py-0.5 text-[11px] text-muted-foreground"
        >
          {day}
        </div>,
      )
    }
    if (entry.role === "player") {
      nodes.push(
        <div key={i} className="flex items-end justify-end gap-1.5 pr-2">
          <Time at={entry.at} read={i < lastNpc} />
          <div
            className={cn(
              "relative max-w-[75%] whitespace-pre-wrap break-words rounded-2xl rounded-tr-none bg-primary px-3 py-2 text-sm text-primary-foreground",
              PLAYER_TAIL,
            )}
          >
            {entry.text}
          </div>
        </div>,
      )
      return
    }
    nodes.push(
      <div key={i} className="flex items-start gap-2">
        <ScenarioAvatar avatar={avatar} className="size-9" />
        <div className="flex min-w-0 flex-1 flex-col items-start gap-1 pl-2">
          <span className="-ml-2 text-[11px] text-muted-foreground">
            {name}
          </span>
          {entry.messages.map((m, j) => (
            <div
              key={`${i}-${j}`}
              className="flex max-w-[85%] items-end gap-1.5"
            >
              <div
                className={cn(
                  "relative whitespace-pre-wrap break-words rounded-2xl bg-card px-3 py-2 text-sm text-card-foreground shadow-sm",
                  j === 0 && cn("rounded-tl-none", NPC_TAIL),
                )}
              >
                {m}
              </div>
              {j === entry.messages.length - 1 && <Time at={entry.at} />}
            </div>
          ))}
        </div>
      </div>,
    )
  })

  return (
    <div ref={root} className="flex flex-col gap-3 px-3 py-4">
      {nodes}
      {trailing}
      {typing && (
        <div data-testid="typing-indicator" className="flex items-start gap-2">
          <ScenarioAvatar avatar={avatar} className="size-9" />
          <div
            className={cn(
              "relative ml-2 mt-5 flex gap-1 rounded-2xl rounded-tl-none bg-card px-3 py-3 shadow-sm",
              NPC_TAIL,
            )}
          >
            <span className="sr-only">輸入中…</span>
            {[0, 150, 300].map((delay) => (
              <span
                key={delay}
                aria-hidden
                className="size-1.5 animate-bounce rounded-full bg-muted-foreground"
                style={{ animationDelay: `${delay}ms` }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
