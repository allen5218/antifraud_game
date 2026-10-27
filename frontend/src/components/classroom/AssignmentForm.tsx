import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import type { AssignmentCreate } from "@/client"
import { expiryOf } from "@/components/trialAdmin/format"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { FRAUD_TYPES, fraudTypeLabel } from "@/lib/fraudTypes"
import { classApi } from "./classroomApi"
import { KIND_LABELS } from "./format"

type Kind = "comprehensive" | "specialized" | "practice" | "pretest"

const SELECT =
  "h-9 w-full rounded-md border border-input bg-background px-2 text-sm"

/** 新增作業：種類決定要填的條件；期限是台灣時間那一天 23:59:59 */
export function AssignmentForm({
  classId,
  onDone,
}: {
  classId: string
  onDone: () => void
}) {
  const queryClient = useQueryClient()
  const [kind, setKind] = useState<Kind>("comprehensive")
  const [requirePass, setRequirePass] = useState(false)
  const [fraudType, setFraudType] = useState<string>(FRAUD_TYPES[0])
  const [practiceType, setPracticeType] = useState("")
  const [counts, setCounts] = useState({ swipe: "", quiz: "", scenario: "" })
  const [title, setTitle] = useState("")
  const [date, setDate] = useState("")

  const params = (): Record<string, unknown> => {
    if (kind === "comprehensive") return { require_pass: requirePass }
    if (kind === "specialized")
      return { fraud_type: fraudType, require_pass: requirePass }
    if (kind === "practice")
      return {
        swipe: Number(counts.swipe) || 0,
        quiz: Number(counts.quiz) || 0,
        scenario: Number(counts.scenario) || 0,
        fraud_type: practiceType || null,
      }
    return {}
  }
  const create = useMutation({
    mutationFn: () => {
      const body: AssignmentCreate = {
        kind,
        title: title.trim() || null,
        params: params(),
        due_at: expiryOf(date),
      }
      return classApi.createAssignment(classId, body)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["classes"] })
      onDone()
    },
  })
  const practiceEmpty =
    kind === "practice" &&
    !(Number(counts.swipe) || Number(counts.quiz) || Number(counts.scenario))
  const ready = date !== "" && !practiceEmpty

  return (
    <form
      className="grid gap-3 rounded-xl border border-border bg-card p-3 text-sm sm:grid-cols-2"
      onSubmit={(event) => {
        event.preventDefault()
        if (ready && !create.isPending) create.mutate()
      }}
    >
      <label className="flex flex-col gap-1">
        <span className="font-medium">種類</span>
        <select
          aria-label="種類"
          className={SELECT}
          value={kind}
          onChange={(event) => setKind(event.target.value as Kind)}
        >
          {(Object.keys(KIND_LABELS) as Kind[]).map((k) => (
            <option key={k} value={k}>
              {KIND_LABELS[k]}
            </option>
          ))}
        </select>
      </label>
      {kind === "specialized" && (
        <label className="flex flex-col gap-1">
          <span className="font-medium">類型</span>
          <select
            aria-label="類型"
            className={SELECT}
            value={fraudType}
            onChange={(event) => setFraudType(event.target.value)}
          >
            {FRAUD_TYPES.map((t) => (
              <option key={t} value={t}>
                {fraudTypeLabel(t)}
              </option>
            ))}
          </select>
        </label>
      )}
      {(kind === "comprehensive" || kind === "specialized") && (
        <label className="flex items-center gap-2 sm:col-span-2">
          <input
            type="checkbox"
            className="size-4 accent-primary"
            checked={requirePass}
            onChange={(event) => setRequirePass(event.target.checked)}
          />
          要過關（70 分）
        </label>
      )}
      {kind === "practice" && (
        <>
          {(
            [
              ["swipe", "滑卡（張）"],
              ["quiz", "訊息判讀（題）"],
              ["scenario", "情境對抗（場）"],
            ] as const
          ).map(([key, label]) => (
            <div key={key} className="flex flex-col gap-1">
              <label htmlFor={`assignment-${key}`} className="font-medium">
                {label}
              </label>
              <Input
                id={`assignment-${key}`}
                aria-label={label}
                type="number"
                min={0}
                max={500}
                inputMode="numeric"
                value={counts[key]}
                onChange={(event) =>
                  setCounts({ ...counts, [key]: event.target.value })
                }
              />
            </div>
          ))}
          <label className="flex flex-col gap-1">
            <span className="font-medium">限定類型</span>
            <select
              aria-label="限定類型"
              className={SELECT}
              value={practiceType}
              onChange={(event) => setPracticeType(event.target.value)}
            >
              <option value="">不限</option>
              {FRAUD_TYPES.map((t) => (
                <option key={t} value={t}>
                  {fraudTypeLabel(t)}
                </option>
              ))}
            </select>
          </label>
        </>
      )}
      <div className="flex flex-col gap-1">
        <label htmlFor="assignment-title" className="font-medium">
          名稱（留空會自動產生）
        </label>
        <Input
          id="assignment-title"
          aria-label="名稱"
          value={title}
          maxLength={100}
          onChange={(event) => setTitle(event.target.value)}
        />
      </div>
      <div className="flex flex-col gap-1">
        <label htmlFor="assignment-due" className="font-medium">
          最後一天
        </label>
        <Input
          id="assignment-due"
          aria-label="最後一天"
          type="date"
          value={date}
          onChange={(event) => setDate(event.target.value)}
        />
      </div>
      {practiceEmpty && (
        <p className="text-muted-foreground sm:col-span-2">
          三種練習至少填一種的數量。
        </p>
      )}
      {create.isError && (
        <p role="alert" className="text-scam sm:col-span-2">
          新增失敗，請檢查條件再試一次。
        </p>
      )}
      <Button
        type="submit"
        className="sm:col-span-2"
        disabled={!ready || create.isPending}
      >
        新增作業
      </Button>
    </form>
  )
}
