import { motion } from "framer-motion"
import type { ReactNode } from "react"

export type ChatEntry =
  | { role: "npc"; messages: string[]; decision_point: string | null }
  | { role: "player"; text: string }

/** 後端 history 是寬鬆 dict;窄化成 ChatEntry */
export function toChatEntries(
  history: Array<Record<string, unknown>>,
): ChatEntry[] {
  return history.map((e) =>
    e.role === "npc"
      ? {
          role: "npc" as const,
          messages: (e.messages as string[]) ?? [],
          decision_point: (e.decision_point as string | null) ?? null,
        }
      : { role: "player" as const, text: (e.text as string) ?? "" },
  )
}

interface MessageListProps {
  entries: ChatEntry[]
  typing: boolean
  /** 渲染在最後一則 npc 訊息之後(用於內嵌 ActionCard) */
  trailing?: ReactNode
}

export function MessageList({ entries, typing, trailing }: MessageListProps) {
  return (
    <div className="flex flex-col gap-2 px-3 py-4">
      {entries.map((entry, i) =>
        entry.role === "npc" ? (
          entry.messages.map((m, j) => (
            <motion.div
              key={`${i}-${j}`}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="max-w-[78%] self-start rounded-2xl rounded-tl-sm bg-background px-3 py-2 text-sm shadow-sm"
            >
              {m}
            </motion.div>
          ))
        ) : (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-[78%] self-end rounded-2xl rounded-tr-sm bg-green-200 px-3 py-2 text-sm dark:bg-green-900"
          >
            {entry.text}
          </motion.div>
        ),
      )}
      {trailing}
      {typing && (
        <div
          data-testid="typing-indicator"
          className="self-start rounded-2xl bg-background px-3 py-2 text-sm text-muted-foreground shadow-sm"
        >
          輸入中…
        </div>
      )}
    </div>
  )
}
