import { motion } from "framer-motion"
import { Eye, ShieldAlert } from "lucide-react"
import type { ReactNode } from "react"
import { detectInfluenceCues } from "@/lib/cialdini"

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
          messages:
            (e.messages as string[]) ??
            (typeof e.content === "string" ? [e.content] : []),
          decision_point: (e.decision_point as string | null) ?? null,
        }
      : {
          role: "player" as const,
          text: (e.text as string) ?? (e.content as string) ?? "",
        },
  )
}

interface MessageListProps {
  entries: ChatEntry[]
  typing: boolean
  /** 渲染在最後一則 npc 訊息之後(用於內嵌 ActionCard) */
  trailing?: ReactNode
  /** 是否開啟席爾迪尼 7 大說服槓桿透視鏡 */
  showCialdiniLens?: boolean
}

export function MessageList({
  entries,
  typing,
  trailing,
  showCialdiniLens = false,
}: MessageListProps) {
  return (
    <div className="flex flex-col gap-3.5 px-3 py-4">
      {entries.map((entry, i) =>
        entry.role === "npc" ? (
          entry.messages.map((m, j) => {
            const cues = showCialdiniLens ? detectInfluenceCues(m) : []
            return (
              <motion.div
                key={`${i}-${j}`}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col gap-1.5 max-w-[85%] self-start"
              >
                <div className="rounded-2xl rounded-tl-xs bg-slate-900/95 text-slate-100 px-3.5 py-2.5 text-sm shadow-sm border border-white/10 leading-relaxed break-words">
                  {m}
                </div>
                {showCialdiniLens && cues.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex flex-col gap-1 rounded-xl bg-slate-950/90 border border-amber-500/40 p-2.5 text-[11px] text-slate-200 shadow-md backdrop-blur-md"
                  >
                    <div className="flex items-center gap-1 font-semibold text-amber-400">
                      <Eye className="size-3.5 shrink-0" />
                      <span>心理說服槓桿透視鏡（後台除錯）</span>
                    </div>
                    {cues.map((cue, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg bg-black/40 p-2 border border-slate-800"
                      >
                        <div className="flex items-center gap-1 font-medium text-amber-300">
                          <ShieldAlert className="size-3 shrink-0 text-rose-400" />
                          <span>槓桿：{cue.leverName}</span>
                          <span className="text-[10px] text-slate-400">
                            (「{cue.matchedText}」)
                          </span>
                        </div>
                        <div className="mt-1 text-slate-300 leading-relaxed">
                          <span className="text-slate-400">話術陷阱：</span>
                          {cue.trap}
                        </div>
                        <div className="mt-0.5 text-emerald-300 leading-relaxed">
                          <span className="text-slate-400">破解煞車：</span>
                          {cue.counter}
                        </div>
                      </div>
                    ))}
                  </motion.div>
                )}
              </motion.div>
            )
          })
        ) : (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-[80%] self-end rounded-2xl rounded-tr-xs bg-[#06C755] text-white px-3.5 py-2.5 text-sm font-medium shadow-sm leading-relaxed break-words"
          >
            {entry.text}
          </motion.div>
        ),
      )}
      {trailing}
      {typing && (
        <div
          data-testid="typing-indicator"
          className="self-start rounded-2xl rounded-tl-xs bg-slate-900/80 border border-white/10 px-3.5 py-2 text-xs text-slate-400 shadow-sm animate-pulse flex items-center gap-1.5"
        >
          <span className="size-1.5 rounded-full bg-[#06C755] animate-ping" />
          <span>對方正在輸入訊息…</span>
        </div>
      )}
    </div>
  )
}
