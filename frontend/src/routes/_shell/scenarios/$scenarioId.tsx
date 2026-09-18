import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import type { ScenarioJudgeResponse } from "@/client"
import { LineChatWrapper } from "@/components/line/LineChatWrapper"
import { ActionCard } from "@/components/scenario/ActionCard"
import { JudgeSheet } from "@/components/scenario/JudgeSheet"
import { FRAUD_TYPE_LABELS, OUTCOME_BADGES } from "@/components/scenario/labels"
import { MessageList, toChatEntries } from "@/components/scenario/MessageList"
import { ResultSheet } from "@/components/scenario/ResultSheet"
import { VerificationToolsModal } from "@/components/scenario/VerificationToolsModal"
import {
  useJudge,
  useNewScenario,
  useScenario,
  useSendMessage,
  useVerifyScenario,
} from "@/hooks/useScenario"

export const Route = createFileRoute("/_shell/scenarios/$scenarioId")({
  component: ScenarioChatPage,
})

/** 拒絕行動卡時代替玩家送出的婉拒訊息(拒絕=不終局、繼續聊) */
const REFUSE_TEXT = "先不用了,我再想想。"

function ScenarioChatPage() {
  const { scenarioId } = Route.useParams()
  const navigate = useNavigate()
  const { data: detail, isPending } = useScenario(scenarioId)
  const sendM = useSendMessage(scenarioId)
  const judgeM = useJudge(scenarioId)
  const verifyM = useVerifyScenario(scenarioId)
  const newM = useNewScenario()
  const [input, setInput] = useState("")
  const [judgeOpen, setJudgeOpen] = useState(false)
  const [verifyOpen, setVerifyOpen] = useState(false)
  const [result, setResult] = useState<ScenarioJudgeResponse | null>(null)

  if (isPending || !detail) {
    return (
      <p className="py-12 text-center text-xs text-muted-foreground">載入中…</p>
    )
  }

  const entries = toChatEntries(detail.history)
  const lastNpc = [...entries].reverse().find((e) => e.role === "npc")
  const decisionPoint =
    detail.status === "active" && lastNpc?.role === "npc"
      ? lastNpc.decision_point
      : null
  const turnsLeft = detail.max_turns - detail.player_turns
  const inputLocked =
    detail.status !== "active" || turnsLeft <= 0 || sendM.isPending

  const send = (text: string, opts: { clearInput?: boolean } = {}) => {
    const trimmed = text.trim()
    if (!trimmed || inputLocked) return
    sendM.mutate(trimmed, {
      onSuccess: () => {
        if (opts.clearInput) setInput("")
      },
    })
  }
  const judge = (action: "report" | "comply" | "safe_exit") => {
    if (judgeM.isPending) return
    setJudgeOpen(false)
    judgeM.mutate(action, { onSuccess: (data) => setResult(data) })
  }

  return (
    <LineChatWrapper
      title={detail.display_name}
      subtitle={`● ${FRAUD_TYPE_LABELS[detail.fraud_type] ?? "其他類型"} (${detail.status === "active" ? `剩 ${turnsLeft} 回合` : "已完成"})`}
      avatarUrl={`https://api.dicebear.com/7.x/bottts/svg?seed=${detail.id}`}
      onReportToLineBot={() => setVerifyOpen(true)}
    >
      <div className="flex h-full flex-col">
        {/* header:返回 + 身份 + 下判斷 */}
        <div className="flex items-center gap-2 border-b border-border bg-background/80 backdrop-blur p-2 rounded-xl">
          <button
            type="button"
            onClick={() => navigate({ to: "/scenarios" })}
            className="px-1 text-lg text-muted-foreground"
            aria-label="返回"
          >
            ‹
          </button>
          <span className="text-xl">{detail.avatar}</span>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-bold">
              {detail.display_name}
            </span>
          </span>
          {detail.status === "active" ? (
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => setVerifyOpen(true)}
                className="rounded-full border border-amber-300 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700 hover:bg-amber-100 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-300"
              >
                🔍 查證 ({detail.unlocked_evidence?.length ?? 0})
              </button>
              <button
                type="button"
                onClick={() => setJudgeOpen(true)}
                data-testid="judge-button"
                className="rounded-full border border-border bg-muted px-3 py-1 text-xs font-semibold"
              >
                ⚖️ 下判斷
              </button>
            </div>
          ) : (
            detail.outcome && (
              <span
                className={`text-[11px] font-bold ${
                  OUTCOME_BADGES[detail.outcome]?.tone === "win"
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {OUTCOME_BADGES[detail.outcome]?.label}
              </span>
            )
          )}
        </div>

      {/* 訊息流 */}
      <div className="flex-1 overflow-y-auto bg-muted/40">
        <MessageList
          entries={entries}
          typing={sendM.isPending}
          trailing={
            decisionPoint && (
              <ActionCard
                text={decisionPoint}
                onComply={() => judge("comply")}
                onRefuse={() => send(REFUSE_TEXT)}
                disabled={judgeM.isPending || sendM.isPending}
                refuseDisabled={turnsLeft <= 0}
              />
            )
          }
        />
      </div>

      {/* 底部:輸入框(active)或開新對話(completed) */}
      {detail.status === "active" ? (
        <div className="border-t border-border bg-background p-2">
          {turnsLeft <= 0 && (
            <p className="pb-1 text-center text-[11px] text-amber-600">
              回覆次數用完了——點右上「⚖️ 下判斷」做出決定
            </p>
          )}
          {sendM.isError && (
            <p className="pb-1 text-center text-[11px] text-red-600">
              訊息沒送出,請再試一次
            </p>
          )}
          <form
            className="flex items-center gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              send(input, { clearInput: true })
            }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={inputLocked}
              placeholder={
                turnsLeft > 0 ? `輸入訊息…(剩 ${turnsLeft} 次)` : "請下判斷"
              }
              className="min-w-0 flex-1 rounded-full bg-muted px-4 py-2 text-sm outline-none disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={inputLocked || !input.trim()}
              className="flex size-9 shrink-0 items-center justify-center rounded-full bg-green-500 text-white disabled:opacity-50"
              aria-label="送出"
            >
              ➤
            </button>
          </form>
        </div>
      ) : (
        <div className="border-t border-border bg-background p-3">
          <button
            type="button"
            disabled={newM.isPending}
            onClick={() =>
              newM.mutate(detail.fraud_type, {
                onSuccess: (item) =>
                  navigate({
                    to: "/scenarios/$scenarioId",
                    params: { scenarioId: item.id },
                  }),
              })
            }
            className="w-full rounded-xl bg-foreground py-2.5 text-sm font-bold text-background disabled:opacity-50"
          >
            開新對話 ›
          </button>
        </div>
      )}

      <VerificationToolsModal
        open={verifyOpen}
        onClose={() => setVerifyOpen(false)}
        tools={detail.available_tools ?? []}
        unlockedEvidence={detail.unlocked_evidence ?? []}
        onVerify={(toolId) => verifyM.mutate(toolId)}
        isVerifying={verifyM.isPending}
      />
      <JudgeSheet
        open={judgeOpen}
        onClose={() => setJudgeOpen(false)}
        onJudge={judge}
      />
      {result && (
        <ResultSheet
          result={result}
          onBack={() => {
            setResult(null)
            navigate({ to: "/scenarios" })
          }}
          onGoAssets={() => navigate({ to: "/assets" })}
        />
      )}
    </div>
  </LineChatWrapper>
)
}
