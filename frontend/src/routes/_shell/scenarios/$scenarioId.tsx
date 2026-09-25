import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { ChevronLeft, Scale, SendHorizontal } from "lucide-react"
import { useState } from "react"
import type { ScenarioJudgeResponse } from "@/client"
import { ActionCard } from "@/components/scenario/ActionCard"
import { JudgeSheet } from "@/components/scenario/JudgeSheet"
import { MessageList, toChatEntries } from "@/components/scenario/MessageList"
import { OutcomeBadge } from "@/components/scenario/OutcomeBadge"
import { ResultSheet } from "@/components/scenario/ResultSheet"
import { ScenarioAvatar } from "@/components/scenario/ScenarioAvatar"
import { usePracticeProfile } from "@/hooks/usePractice"
import {
  newScenarioError,
  useJudge,
  useNewScenario,
  useScenario,
  useScenarioInbox,
  useSendMessage,
} from "@/hooks/useScenario"
import { fraudTypeLabel } from "@/lib/fraudTypes"

export const Route = createFileRoute("/_shell/scenarios/$scenarioId")({
  component: ScenarioChatRoute,
})

/** 換場時整個重新掛載:草稿、判斷視窗、結算卡、提示都不會帶到下一場。 */
function ScenarioChatRoute() {
  const { scenarioId } = Route.useParams()
  return <ScenarioChatPage key={scenarioId} scenarioId={scenarioId} />
}

/** 拒絕行動卡時代替玩家送出的婉拒訊息(拒絕=不終局、繼續聊) */
const REFUSE_TEXT = "先不用了，我再想想。"

function ScenarioChatPage({ scenarioId }: { scenarioId: string }) {
  const navigate = useNavigate()
  const { data: detail, isPending } = useScenario(scenarioId)
  const sendM = useSendMessage(scenarioId)
  const judgeM = useJudge(scenarioId)
  const newM = useNewScenario()
  // 收件匣用來找「這一類還沒聊完的那場」;練習重點決定結束後推薦哪一類
  const inbox = useScenarioInbox()
  const { data: profile } = usePracticeProfile()
  const [input, setInput] = useState("")
  const [judgeOpen, setJudgeOpen] = useState(false)
  const [result, setResult] = useState<ScenarioJudgeResponse | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

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
    detail.status !== "active" || turnsLeft <= 0 || sendM.isPending || judgeOpen

  const send = (text: string, opts: { clearInput?: boolean } = {}) => {
    const trimmed = text.trim()
    if (!trimmed || inputLocked) return
    sendM.mutate(trimmed, {
      onSuccess: () => {
        if (opts.clearInput) setInput("")
      },
    })
  }
  const openScenario = (id: string) =>
    navigate({ to: "/scenarios/$scenarioId", params: { scenarioId: id } })
  const startNew = (fraudType: string) => {
    if (newM.isPending) return
    // 這一場剛判斷完,收件匣可能還沒重抓、仍標成進行中,所以排除自己
    const active = inbox.data?.find(
      (row) =>
        row.fraud_type === fraudType &&
        row.status === "active" &&
        row.id !== scenarioId,
    )
    if (active) {
      openScenario(active.id)
      return
    }
    setNotice(null)
    newM.mutate(fraudType, {
      onSuccess: (item) => openScenario(item.id),
      onError: (err) => setNotice(newScenarioError(err, fraudType)),
    })
  }
  const focusType = profile?.focus_type ?? null

  const judge = (action: "report" | "comply") => {
    if (judgeM.isPending) return
    setJudgeOpen(false)
    judgeM.mutate(action, { onSuccess: (data) => setResult(data) })
  }

  return (
    <div className="flex h-full flex-col">
      {/* header:返回 + 身份 + 下判斷 */}
      <div className="flex items-center gap-2 border-b border-border bg-background px-3 py-2">
        <button
          type="button"
          onClick={() => navigate({ to: "/scenarios" })}
          className="-ml-1 rounded-full p-1 text-muted-foreground hover:bg-muted"
          aria-label="返回"
        >
          <ChevronLeft aria-hidden className="size-5" />
        </button>
        <ScenarioAvatar avatar={detail.avatar} className="size-8" />
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-bold">
            {detail.display_name}
          </span>
          <span className="text-[10px] font-semibold text-primary">
            {fraudTypeLabel(detail.fraud_type)}
          </span>
        </span>
        {detail.status === "active" ? (
          <button
            type="button"
            onClick={() => setJudgeOpen(true)}
            data-testid="judge-button"
            className="flex items-center gap-1 rounded-full border border-primary/50 bg-primary/10 px-3 py-1 text-xs font-bold text-primary"
          >
            <Scale aria-hidden className="size-3.5" />
            下判斷
          </button>
        ) : (
          detail.outcome && (
            <OutcomeBadge outcome={detail.outcome} className="text-[11px]" />
          )
        )}
      </div>

      {/* 訊息流 */}
      <div className="flex-1 overflow-y-auto bg-surface-2">
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
            <p className="pb-1 text-center text-[11px] font-semibold text-warning">
              回覆次數用完了，請按右上角的「下判斷」
            </p>
          )}
          {sendM.isError && (
            <p className="pb-1 text-center text-[11px] text-destructive">
              訊息沒送出，請再試一次
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
                turnsLeft > 0
                  ? `輸入訊息…（還能回 ${turnsLeft} 次）`
                  : "請下判斷"
              }
              className="min-w-0 flex-1 rounded-full bg-muted px-4 py-2 text-sm outline-none disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={inputLocked || !input.trim()}
              className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground disabled:opacity-50"
              aria-label="送出"
            >
              <SendHorizontal aria-hidden className="size-4" />
            </button>
          </form>
        </div>
      ) : (
        <div className="border-t border-border bg-background p-3">
          <button
            type="button"
            disabled={newM.isPending}
            onClick={() => startNew(detail.fraud_type)}
            className="w-full rounded-xl bg-primary py-2.5 text-sm font-bold text-primary-foreground disabled:opacity-50"
          >
            開新對話
          </button>
          {notice && !result && (
            <p role="alert" className="mt-2 text-center text-[11px] text-scam">
              {notice}
            </p>
          )}
        </div>
      )}

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
          next={
            focusType
              ? {
                  fraudType: focusType,
                  onStart: () => startNew(focusType),
                  pending: newM.isPending,
                  notice,
                }
              : undefined
          }
        />
      )}
    </div>
  )
}
