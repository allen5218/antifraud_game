import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { useState } from "react"
import type { MyAssignment, MyClassPublic } from "@/client"
import { taipeiDate } from "@/components/trialAdmin/format"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { HOME_SUMMARY_KEY } from "@/hooks/useHomeSummary"
import { classApi } from "./classroomApi"
import { STATUS_LABELS } from "./format"

export const MY_CLASSES_KEY = ["classes", "mine"] as const

type Target =
  | "/exam"
  | "/pretest"
  | "/quick/swipe"
  | "/quick/quiz"
  | "/scenarios"

const PRACTICE_TARGETS: [string, Target][] = [
  ["滑卡", "/quick/swipe"],
  ["訊息判讀", "/quick/quiz"],
  ["情境對抗", "/scenarios"],
]

/** 「去做」連到哪裡；練習量連到第一個還沒練滿的那一種 */
export function assignmentTarget(a: MyAssignment): Target {
  if (a.kind === "comprehensive" || a.kind === "specialized") return "/exam"
  if (a.kind === "pretest") return "/pretest"
  for (const part of a.progress_text.split("、")) {
    const match = part.match(/^(\S+) (\d+)／(\d+)$/)
    if (match && Number(match[2]) < Number(match[3])) {
      const target = PRACTICE_TARGETS.find(([label]) => label === match[1])
      if (target) return target[1]
    }
  }
  return "/quick/swipe"
}

/** 學生的班級作業：加入班級、填學號名字、看作業進度 */
export function Classwork() {
  const classes = useQuery({ queryKey: MY_CLASSES_KEY, queryFn: classApi.mine })
  return (
    <div className="flex flex-col gap-4 pb-8">
      <header>
        <h1 className="text-2xl font-bold">班級作業</h1>
        <p className="text-sm text-muted-foreground">
          老師出的作業會列在這裡，做完會自動變成完成。
        </p>
      </header>
      {classes.isPending && <output>正在載入…</output>}
      {classes.isError && (
        <p role="alert" className="text-scam">
          讀不到班級，請再試一次。
        </p>
      )}
      {classes.data?.length === 0 && (
        <p className="text-muted-foreground">
          還沒有加入班級。掃老師給的 QR code，或在下面輸入班級代碼。
        </p>
      )}
      {classes.data?.map((c) => (
        <ClassSection key={c.id} classroom={c} />
      ))}
      <JoinByCode />
    </div>
  )
}

function ClassSection({ classroom: c }: { classroom: MyClassPublic }) {
  const claimed = Boolean(c.student_number && c.student_name)
  const [editing, setEditing] = useState(false)
  return (
    <section
      data-testid={`class-${c.id}`}
      className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4"
    >
      <div>
        <h2 className="text-lg font-bold">{c.name}</h2>
        <p className="text-sm text-muted-foreground">
          {c.teacher_name}
          {claimed ? `・${c.student_number} ${c.student_name}` : ""}
        </p>
      </div>
      {!claimed || editing ? (
        <ClaimForm classroom={c} onDone={() => setEditing(false)} />
      ) : (
        <>
          {c.assignments.length === 0 ? (
            <p className="text-muted-foreground">老師還沒出作業。</p>
          ) : (
            <ul className="flex flex-col divide-y divide-border">
              {c.assignments.map((a) => (
                <AssignmentRow key={a.id} assignment={a} />
              ))}
            </ul>
          )}
          <Button
            variant="ghost"
            className="self-start text-muted-foreground"
            onClick={() => setEditing(true)}
          >
            改學號名字
          </Button>
        </>
      )}
    </section>
  )
}

function AssignmentRow({ assignment: a }: { assignment: MyAssignment }) {
  const open = a.status === "todo" || a.status === "overdue"
  return (
    <li className="flex flex-wrap items-center gap-x-3 gap-y-1 py-2 text-sm">
      <span className="flex min-w-0 flex-1 flex-col">
        <span className="font-bold">{a.title}</span>
        <span className="text-xs text-muted-foreground">
          {taipeiDate(a.due_at)} 截止
          {open && a.progress_text !== STATUS_LABELS.todo
            ? `・${a.progress_text}`
            : ""}
        </span>
      </span>
      <span
        className={
          a.status === "done" || a.status === "late"
            ? "text-legit"
            : a.status === "overdue"
              ? "text-scam"
              : "text-muted-foreground"
        }
      >
        {STATUS_LABELS[a.status] ?? a.status}
      </span>
      {open && (
        <Link
          to={assignmentTarget(a)}
          className="rounded-lg bg-primary px-3 py-1.5 text-xs font-bold text-primary-foreground"
        >
          去做
        </Link>
      )}
    </li>
  )
}

function ClaimForm({
  classroom: c,
  onDone,
}: {
  classroom: MyClassPublic
  onDone: () => void
}) {
  const queryClient = useQueryClient()
  const [number, setNumber] = useState(c.student_number ?? "")
  const [name, setName] = useState(c.student_name ?? "")
  const claim = useMutation({
    mutationFn: () =>
      classApi.claim(c.id, {
        student_number: number.trim(),
        student_name: name.trim(),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MY_CLASSES_KEY })
      queryClient.invalidateQueries({ queryKey: HOME_SUMMARY_KEY })
      onDone()
    },
  })
  const ready = number.trim() !== "" && name.trim() !== ""
  return (
    <form
      className="flex flex-col gap-2 text-sm"
      onSubmit={(event) => {
        event.preventDefault()
        if (ready && !claim.isPending) claim.mutate()
      }}
    >
      <p>先填學號和名字，才看得到老師出的作業。只有老師看得到。</p>
      <label htmlFor={`claim-number-${c.id}`} className="font-medium">
        學號
      </label>
      <Input
        id={`claim-number-${c.id}`}
        value={number}
        maxLength={32}
        onChange={(event) => setNumber(event.target.value)}
      />
      <label htmlFor={`claim-name-${c.id}`} className="font-medium">
        名字
      </label>
      <Input
        id={`claim-name-${c.id}`}
        value={name}
        maxLength={50}
        onChange={(event) => setName(event.target.value)}
      />
      {claim.isError && (
        <p role="alert" className="text-scam">
          送出失敗，請再試一次。
        </p>
      )}
      <Button type="submit" disabled={!ready || claim.isPending}>
        送出
      </Button>
    </form>
  )
}

function JoinByCode() {
  const queryClient = useQueryClient()
  const [code, setCode] = useState("")
  const join = useMutation({
    mutationFn: () => classApi.join({ code: code.trim().toUpperCase() }),
    onSuccess: () => {
      setCode("")
      queryClient.invalidateQueries({ queryKey: MY_CLASSES_KEY })
      queryClient.invalidateQueries({ queryKey: HOME_SUMMARY_KEY })
    },
  })
  return (
    <form
      className="flex flex-wrap items-end gap-2 text-sm"
      onSubmit={(event) => {
        event.preventDefault()
        if (code.trim() && !join.isPending) join.mutate()
      }}
    >
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <label htmlFor="class-code" className="font-medium">
          班級代碼
        </label>
        <Input
          id="class-code"
          value={code}
          maxLength={6}
          autoCapitalize="characters"
          onChange={(event) => setCode(event.target.value)}
        />
      </div>
      <Button type="submit" disabled={!code.trim() || join.isPending}>
        加入班級
      </Button>
      {join.isError && (
        <p role="alert" className="basis-full text-scam">
          找不到這個班級，或老師已經停止加入。
        </p>
      )}
    </form>
  )
}
