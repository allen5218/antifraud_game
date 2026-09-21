import { createFileRoute, useNavigate } from "@tanstack/react-router"
import {
  FileSearch,
  FileText,
  PauseCircle,
  PlayCircle,
  Scale,
  Send,
  Zap,
} from "lucide-react"
import { useState } from "react"
import type { ScenarioJudgeResponse } from "@/client"
import { LineChatWrapper } from "@/components/line/LineChatWrapper"
import { BranchActionsModal } from "@/components/scenario/BranchActionsModal"
import { JudgeSheet } from "@/components/scenario/JudgeSheet"
import { FRAUD_TYPE_LABELS, OUTCOME_BADGES } from "@/components/scenario/labels"
import { MessageList, toChatEntries } from "@/components/scenario/MessageList"
import { ResultSheet } from "@/components/scenario/ResultSheet"
import { VerificationToolsModal } from "@/components/scenario/VerificationToolsModal"
import {
  useExecuteAction,
  useJudge,
  useNewScenario,
  usePauseScenario,
  useResumeScenario,
  useScenario,
  useSendMessage,
  useVerifyScenario,
} from "@/hooks/useScenario"

export const Route = createFileRoute("/_shell/scenarios/$scenarioId")({
  component: ScenarioChatPage,
})

function ScenarioChatPage() {
  const { scenarioId } = Route.useParams()
  const navigate = useNavigate()
  const { data: detail, isPending, isError, refetch } = useScenario(scenarioId)
  const sendM = useSendMessage(scenarioId)
  const judgeM = useJudge(scenarioId)
  const pauseM = usePauseScenario(scenarioId)
  const resumeM = useResumeScenario(scenarioId)
  const verifyM = useVerifyScenario(scenarioId)
  const executeM = useExecuteAction(scenarioId)
  const newM = useNewScenario()

  const [input, setInput] = useState("")
  const [activeMsgRequestId, setActiveMsgRequestId] = useState<string>(() =>
    crypto.randomUUID(),
  )
  const [conflictError, setConflictError] = useState<string | null>(null)
  const [verifyRequestId, setVerifyRequestId] = useState<string>(() =>
    crypto.randomUUID(),
  )
  const [judgeRequestId, setJudgeRequestId] = useState<string>(() =>
    crypto.randomUUID(),
  )
  const [actionRequestId, setActionRequestId] = useState<string>(() =>
    crypto.randomUUID(),
  )
  const [judgeOpen, setJudgeOpen] = useState(false)
  const [verifyOpen, setVerifyOpen] = useState(false)
  const [actionsOpen, setActionsOpen] = useState(false)
  const [result, setResult] = useState<ScenarioJudgeResponse | null>(null)

  if (isPending) {
    return (
      <p className="py-12 text-center text-xs text-muted-foreground">載入中…</p>
    )
  }

  if (isError || !detail) {
    return (
      <div className="py-12 text-center space-y-3">
        <p className="text-xs text-rose-400">載入對話失敗或事件不存在</p>
        <button
          type="button"
          onClick={() => refetch()}
          className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-white rounded-lg border border-slate-700 transition-colors"
        >
          重新整理
        </button>
      </div>
    )
  }

  const isPaused = detail.status === "paused" || Boolean(detail.is_paused)
  const isActive = detail.status === "active" && !isPaused
  const entries = toChatEntries(detail.history)
  const turnsLeft = detail.max_turns - detail.player_turns
  const inputLocked = !isActive || turnsLeft <= 0 || sendM.isPending

  const send = (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || inputLocked) return
    setConflictError(null)
    sendM.mutate(
      {
        text: trimmed,
        expectedRevision: detail.revision,
        requestId: activeMsgRequestId,
      },
      {
        onSuccess: () => {
          setInput("")
          setActiveMsgRequestId(crypto.randomUUID())
          setConflictError(null)
        },
        onError: (err: any) => {
          if (
            err?.status === 409 ||
            err?.body?.detail?.code === "revision_mismatch"
          ) {
            setConflictError(
              "對話進度已有更新（已同步最新狀態，草稿已保留，請確認後重新送出）",
            )
            refetch()
          } else {
            setConflictError(err?.message || "訊息沒送出，請再試一次")
          }
        },
      },
    )
  }

  const handleVerify = (toolId: string) => {
    verifyM.mutate(
      {
        toolId,
        expectedRevision: detail.revision,
        requestId: verifyRequestId,
      },
      {
        onSuccess: () => {
          setVerifyRequestId(crypto.randomUUID())
        },
        onError: (err: any) => {
          if (err?.status === 409) {
            refetch()
          }
        },
      },
    )
  }

  const handleExecuteAction = (actionId: string) => {
    executeM.mutate(
      {
        actionId,
        expectedRevision: detail.revision,
        requestId: actionRequestId,
      },
      {
        onSuccess: () => {
          setActionRequestId(crypto.randomUUID())
          setActionsOpen(false)
          refetch()
        },
        onError: (err: any) => {
          if (err?.status === 409) {
            setConflictError("對話進度已有更新，已同步最新狀態")
            refetch()
          } else {
            setConflictError(
              err?.message || "執行行動失敗，請確認條件與餘額後重試",
            )
          }
        },
      },
    )
  }

  const judge = (action: "report" | "comply" | "safe_exit" | "pause") => {
    if (judgeM.isPending || pauseM.isPending) return
    setJudgeOpen(false)
    if (action === "pause") {
      pauseM.mutate(
        {
          expectedRevision: detail.revision,
          requestId: judgeRequestId,
        },
        {
          onSuccess: (_data) => {
            setJudgeRequestId(crypto.randomUUID())
            refetch()
          },
          onError: (err: any) => {
            if (err?.status === 409) {
              refetch()
            }
          },
        },
      )
      return
    }

    judgeM.mutate(
      {
        action,
        expectedRevision: detail.revision,
        requestId: judgeRequestId,
      },
      {
        onSuccess: (data) => {
          setJudgeRequestId(crypto.randomUUID())
          setResult(data)
          refetch()
        },
        onError: (err: any) => {
          if (err?.status === 409) {
            refetch()
          }
        },
      },
    )
  }

  const handleResume = () => {
    resumeM.mutate(
      {
        expectedRevision: detail.revision,
        requestId: crypto.randomUUID(),
      },
      {
        onSuccess: () => {
          refetch()
        },
      },
    )
  }

  const subtitleText =
    detail.story_title ?? FRAUD_TYPE_LABELS[detail.fraud_type] ?? "聊天"

  return (
    <LineChatWrapper
      title={detail.display_name}
      subtitle={subtitleText}
      avatarUrl={`https://api.dicebear.com/7.x/bottts/svg?seed=${detail.id}`}
      onBack={() => navigate({ to: "/scenarios" })}
      headerActions={
        isActive ? (
          <div className="flex items-center gap-1.5">
            {detail.available_branch_actions &&
              detail.available_branch_actions.length > 0 && (
                <button
                  type="button"
                  onClick={() => setActionsOpen(true)}
                  data-testid="branch-actions-button"
                  className="flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-600/80 px-2.5 py-1 text-xs font-bold text-white hover:bg-emerald-500 transition-colors shadow-sm"
                  title="執行調查行動或環境應對"
                >
                  <Zap className="size-3.5" />
                  <span className="hidden sm:inline">
                    行動 (
                    {
                      detail.available_branch_actions.filter((a) => a.available)
                        .length
                    }
                    )
                  </span>
                </button>
              )}
            <button
              type="button"
              onClick={() => setVerifyOpen(true)}
              data-testid="verify-action-button"
              className="flex items-center gap-1 rounded-full border border-sky-400/30 bg-sky-600/80 px-2.5 py-1 text-xs font-bold text-white hover:bg-sky-500 transition-colors shadow-sm"
              title="查看資料"
            >
              <FileSearch className="size-3.5" />
              <span className="hidden sm:inline">
                查證 ({detail.unlocked_evidence?.length ?? 0})
              </span>
            </button>
            <button
              type="button"
              onClick={() => setJudgeOpen(true)}
              data-testid="judge-button"
              className="flex items-center gap-1 rounded-full border border-rose-300/40 bg-rose-600 px-3 py-1 text-xs font-bold text-white hover:bg-rose-500 transition-colors shadow-sm"
              title="做出判斷：檢舉、暫停、安全退出或信任"
            >
              <Scale className="size-3.5" />
              <span className="hidden sm:inline">處理</span>
            </button>
          </div>
        ) : isPaused ? (
          <div className="flex items-center gap-1.5">
            <span
              data-testid="header-paused-badge"
              className="text-xs px-2.5 py-1 rounded-full font-bold shadow-sm bg-amber-500 text-slate-950 flex items-center gap-1"
            >
              <PauseCircle className="size-3.5" />
              暫停中
            </span>
          </div>
        ) : (
          detail.outcome && (
            <span
              className={`text-xs px-2.5 py-1 rounded-full font-bold shadow-sm ${
                OUTCOME_BADGES[detail.outcome]?.tone === "win"
                  ? "bg-emerald-500 text-white"
                  : "bg-rose-500 text-white"
              }`}
            >
              {OUTCOME_BADGES[detail.outcome]?.label}
            </span>
          )
        )
      }
    >
      <div className="flex h-full flex-col min-h-0">
        {/* 訊息流：直覺留給用戶，無干擾純淨對話 */}
        <div className="flex-1 overflow-y-auto px-1 py-2">
          <MessageList
            entries={entries}
            typing={sendM.isPending}
            showCialdiniLens={false}
          />
        </div>

        {/* 底部:輸入框(active)、暫停提示(paused)、或開新對話/查看報告(completed) */}
        {isActive ? (
          <div className="border-t border-border bg-background p-2">
            {conflictError && (
              <p className="pb-1 text-center text-[11px] text-amber-400 font-medium">
                {conflictError}
              </p>
            )}

            <form
              className="flex items-center gap-2"
              onSubmit={(e) => {
                e.preventDefault()
                send(input)
              }}
            >
              <input
                value={input}
                onChange={(e) => {
                  setInput(e.target.value)
                  if (conflictError) setConflictError(null)
                }}
                disabled={inputLocked}
                placeholder="輸入訊息…"
                className="min-w-0 flex-1 rounded-full bg-muted px-4 py-2 text-sm outline-none disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={inputLocked || !input.trim()}
                className="flex size-9 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-900 font-bold disabled:opacity-50 hover:bg-white"
                aria-label="送出"
              >
                <Send className="size-3.5" />
              </button>
            </form>
          </div>
        ) : isPaused ? (
          <div className="border-t border-border bg-slate-950 p-3 space-y-2">
            <div className="flex items-center justify-between text-xs text-amber-300">
              <span className="flex items-center gap-1.5 font-bold">
                <PauseCircle className="size-4 text-amber-400" />
                <span>調查已暫停（事證與進度已妥善封存）</span>
              </span>
              <button
                type="button"
                onClick={() => setVerifyOpen(true)}
                className="text-[11px] underline text-sky-400 hover:text-sky-300"
              >
                檢視事證 ({detail.unlocked_evidence?.length ?? 0})
              </button>
            </div>
            <button
              type="button"
              disabled={resumeM.isPending}
              onClick={handleResume}
              data-testid="resume-button"
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-amber-500 hover:bg-amber-400 py-2.5 text-sm font-bold text-slate-950 disabled:opacity-50 transition-colors"
            >
              <PlayCircle className="size-4" />
              <span>繼續對話 ›</span>
            </button>
          </div>
        ) : (
          <div className="border-t border-border bg-background p-3 space-y-2">
            {detail.source_adaptation_mark && (
              <p className="text-center text-[11px] text-slate-400">
                本案素材：{detail.source_adaptation_mark}
              </p>
            )}
            {detail.learning_objective && (
              <p className="text-center text-[11px] text-slate-300 bg-slate-900/60 p-2 rounded-lg border border-white/5">
                核心學習目標：{detail.learning_objective}
              </p>
            )}
            <div className="flex gap-2">
              {detail.terminal_result && (
                <button
                  type="button"
                  onClick={() => setResult(detail.terminal_result || null)}
                  data-testid="view-terminal-result-button"
                  className="flex-1 flex items-center justify-center gap-1.5 rounded-xl border border-border bg-muted/60 py-2.5 text-sm font-bold text-foreground hover:bg-muted"
                >
                  <FileText className="size-4" />
                  <span>查看結案報告</span>
                </button>
              )}
              <button
                type="button"
                disabled={newM.isPending}
                onClick={() =>
                  newM.mutate(
                    {
                      contactId: detail.contact_id ?? undefined,
                      fraudType: detail.fraud_type,
                      requestId: crypto.randomUUID(),
                    },
                    {
                      onSuccess: (item) =>
                        navigate({
                          to: "/scenarios/$scenarioId",
                          params: { scenarioId: item.id },
                        }),
                    },
                  )
                }
                className="flex-1 rounded-xl bg-foreground py-2.5 text-sm font-bold text-background disabled:opacity-50"
              >
                開新對話 ›
              </button>
            </div>
          </div>
        )}

        <BranchActionsModal
          open={actionsOpen}
          onClose={() => setActionsOpen(false)}
          actions={detail.available_branch_actions || []}
          onExecute={handleExecuteAction}
          isExecuting={executeM.isPending}
          onGoShop={() => navigate({ to: "/scenarios" })}
        />

        <VerificationToolsModal
          open={verifyOpen}
          onClose={() => setVerifyOpen(false)}
          tools={detail.available_tools || []}
          unlockedEvidence={detail.unlocked_evidence || []}
          onVerify={handleVerify}
          isVerifying={verifyM.isPending}
          onUseEvidenceInChat={(text) => {
            setVerifyOpen(false)
            setInput(text)
          }}
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
