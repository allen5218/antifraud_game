import { useQuery } from "@tanstack/react-query"
import { SendHorizontal } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import type { ExamState } from "@/client"
import { ExamService, ScenarioService } from "@/client/sdk.gen"
import { ActionCard } from "@/components/scenario/ActionCard"
import { JudgeSheet } from "@/components/scenario/JudgeSheet"
import { MessageList, toChatEntries } from "@/components/scenario/MessageList"
import { ScenarioAvatar } from "@/components/scenario/ScenarioAvatar"
import { Button } from "@/components/ui/button"
import { errorCode, examError } from "./exam"

const REFUSE_TEXT = "先不用了，我再想想。"

export function ExamScenario({
  state,
  busy,
  mutate,
  refresh,
}: {
  state: ExamState
  busy: boolean
  mutate: (operation: () => PromiseLike<ExamState>) => Promise<void>
  refresh: () => Promise<unknown>
}) {
  const scenario = state.scenario
  const sid = scenario?.session_id
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const sendLock = useRef(false)
  const pendingSend = useRef<{
    turns: number
    draft: string
    decision: string | null
  } | null>(null)
  const [settledRefuse, setSettledRefuse] = useState<string | null>(null)
  const [judgeOpen, setJudgeOpen] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [judgment, setJudgment] = useState<"report" | "comply" | null>(null)
  const detailQuery = useQuery({
    queryKey: ["exam", "chat", sid],
    queryFn: () => ScenarioService.readScenario({ scenarioId: sid! }),
    enabled: !!sid,
    retry: false,
    refetchOnWindowFocus: true,
  })
  const detail = detailQuery.data
  const entries = detail ? toChatEntries(detail.history) : []
  const last = [...entries].reverse().find((entry) => entry.role === "npc")
  const decision = last?.role === "npc" ? last.decision_point : null
  useEffect(() => {
    const pending = pendingSend.current
    if (!pending || !detail || detail.player_turns <= pending.turns) return
    setInput((current) => (current.trim() === pending.draft ? "" : current))
    setNotice(null)
    if (pending.draft === REFUSE_TEXT) setSettledRefuse(pending.decision)
    pendingSend.current = null
  }, [detail])
  const turns = Math.max(
    0,
    (detail?.max_turns ?? scenario?.max_turns ?? 0) -
      (detail?.player_turns ?? 0),
  )
  const disabled =
    busy ||
    sending ||
    judgment !== null ||
    !detail ||
    detailQuery.isFetching ||
    detailQuery.isError
  const send = async (text: string) => {
    if (sendLock.current || disabled || turns <= 0 || !text.trim() || !sid)
      return
    sendLock.current = true
    setSending(true)
    setNotice(null)
    const before = detail.player_turns
    const draft = text.trim()
    try {
      await ScenarioService.sendMessage({
        scenarioId: sid,
        requestBody: { text: draft },
      })
      pendingSend.current = null
      setInput((current) => (current.trim() === draft ? "" : current))
      try {
        await detailQuery.refetch()
      } catch {
        // 送出已成功，接著重讀失敗不算送出失敗。
      }
    } catch (error) {
      pendingSend.current = { turns: before, draft, decision }
      setNotice(examError(error))
      try {
        if (errorCode(error) === "exam_ended") await refresh()
        else await detailQuery.refetch()
      } catch {
        // 重讀失敗留在畫面上的錯誤提示，不往外拋。
      }
    } finally {
      sendLock.current = false
      setSending(false)
    }
  }
  const judge = (action: "report" | "comply") => {
    if (busy || sendLock.current || !sid) return
    setJudgeOpen(false)
    setJudgment(action)
    void mutate(() =>
      ExamService.scenarioJudge({
        attemptId: state.id,
        requestBody: { session_id: sid, action },
      }),
    )
  }
  if (!scenario) return <p role="alert">情境關卡讀不到，請重新讀取檢測。</p>
  if (!sid)
    return (
      <section className="space-y-4 rounded-2xl border bg-card p-5">
        <h2 className="font-bold">
          情境對抗第 {scenario.index} 場，共 {scenario.count} 場
        </h2>
        <p className="text-sm">
          和對方聊聊，再判斷要不要相信。這場最多回覆 {scenario.max_turns} 次。
        </p>
        <Button
          disabled={busy}
          onClick={() =>
            mutate(() => ExamService.scenarioStart({ attemptId: state.id }))
          }
        >
          開始這場對話
        </Button>
      </section>
    )
  if (!detail)
    return (
      <section>
        {detailQuery.isError ? (
          <>
            <p role="alert">對話讀不到，請再試一次。</p>
            <Button
              onClick={() => {
                void detailQuery.refetch().catch(() => undefined)
              }}
            >
              重新讀取對話
            </Button>
          </>
        ) : (
          <p>正在讀取對話…</p>
        )}
      </section>
    )
  return (
    <section className="overflow-hidden rounded-2xl border bg-card">
      <header className="flex items-center gap-2 border-b p-3">
        <ScenarioAvatar avatar={detail.avatar} className="size-8" />
        <div className="min-w-0 flex-1">
          <h2 className="truncate font-bold">{detail.display_name}</h2>
          <p className="text-xs text-muted-foreground">
            第 {scenario.index}／{scenario.count} 場，還能回覆 {turns} 次
          </p>
        </div>
        <Button
          size="sm"
          variant="outline"
          disabled={disabled}
          onClick={() => setJudgeOpen(true)}
        >
          下判斷
        </Button>
      </header>
      <div className="max-h-[45dvh] overflow-y-auto bg-surface-2">
        <MessageList
          entries={entries}
          typing={sending}
          trailing={
            last?.role === "npc" && last.decision_point && !judgment ? (
              <ActionCard
                text={last.decision_point}
                onComply={() => judge("comply")}
                onRefuse={() => send(REFUSE_TEXT)}
                disabled={disabled}
                refuseDisabled={
                  turns <= 0 ||
                  (settledRefuse !== null && decision === settledRefuse)
                }
              />
            ) : null
          }
        />
      </div>
      {notice && (
        <p role="alert" className="p-3 text-sm text-scam">
          {notice}
        </p>
      )}
      {detailQuery.isError && (
        <div role="alert" className="p-3 text-sm text-scam">
          對話進度讀不到，請先重新讀取。
          <Button
            variant="outline"
            onClick={() => {
              void detailQuery.refetch().catch(() => undefined)
            }}
          >
            重新讀取對話
          </Button>
        </div>
      )}
      {judgment ? (
        <div className="space-y-2 p-3">
          <p className="text-sm">
            正在確認判斷。若送出失敗，可以重送同一個判斷。
          </p>
          <Button disabled={busy || sending} onClick={() => judge(judgment)}>
            重送原判斷
          </Button>
          <Button
            disabled={busy}
            variant="outline"
            onClick={() => {
              void refresh().catch(() => {
                setNotice(
                  (current) => current ?? "檢測進度讀不到，請再試一次。",
                )
              })
            }}
          >
            重新讀取檢測
          </Button>
        </div>
      ) : (
        <form
          className="flex gap-2 border-t p-3"
          onSubmit={(event) => {
            event.preventDefault()
            void send(input)
          }}
        >
          <input
            aria-label="對話訊息"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            disabled={
              disabled || turns <= 0 || judgeOpen || detailQuery.isError
            }
            placeholder={turns > 0 ? "輸入訊息…" : "回覆次數用完了，請下判斷"}
            className="min-w-0 flex-1 rounded-full bg-muted px-4 py-2 text-sm disabled:opacity-50"
          />
          <Button
            type="submit"
            size="icon"
            aria-label="送出訊息"
            disabled={
              disabled ||
              turns <= 0 ||
              !input.trim() ||
              judgeOpen ||
              detailQuery.isError
            }
          >
            <SendHorizontal aria-hidden className="size-4" />
          </Button>
        </form>
      )}
      <JudgeSheet
        open={judgeOpen}
        disabled={busy || sending}
        onClose={() => setJudgeOpen(false)}
        onJudge={judge}
        description={
          scenario.index < scenario.count
            ? "判斷後這場對話就結束，接著進下一場。"
            : "判斷後這場對話就結束，接著完成檢測。"
        }
      />
    </section>
  )
}
