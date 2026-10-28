import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ChevronDown, Trash2 } from "lucide-react"
import { useState } from "react"
import type { AssignmentSummary, ClassOverview, PendingStudent } from "@/client"
import { taipeiDate } from "@/components/trialAdmin/format"
import { Button } from "@/components/ui/button"
import { classApi } from "./classroomApi"
import { STATUS_LABELS, studentLabel } from "./format"

/** 每份作業一張卡：完成人數；展開是還沒完成與遲交的名單 */
export function AssignmentList({
  classId,
  data,
}: {
  classId: string
  data: ClassOverview
}) {
  if (data.assignments.length === 0)
    return <p className="text-muted-foreground">還沒有作業。</p>
  return (
    <ul className="flex flex-col gap-2">
      {data.assignments.map((a) => (
        <AssignmentCard
          key={a.id}
          classId={classId}
          assignment={a}
          total={data.member_count}
        />
      ))}
    </ul>
  )
}

function StudentRows({ rows }: { rows: PendingStudent[] }) {
  return (
    <ul className="flex flex-col divide-y divide-border">
      {rows.map((s) => (
        <li
          key={s.user_id}
          className="flex flex-wrap justify-between gap-x-3 py-1"
        >
          <span>{studentLabel(s)}</span>
          <span className="text-muted-foreground">
            {STATUS_LABELS[s.status] ?? s.status}
            {s.status !== "late" && s.progress_text !== STATUS_LABELS.todo
              ? `・${s.progress_text}`
              : ""}
          </span>
        </li>
      ))}
    </ul>
  )
}

function AssignmentCard({
  classId,
  assignment: a,
  total,
}: {
  classId: string
  assignment: AssignmentSummary
  total: number
}) {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const remove = useMutation({
    mutationFn: () => classApi.deleteAssignment(classId, a.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["classes"] }),
  })
  return (
    <li
      data-testid={`assignment-${a.id}`}
      className="flex flex-col gap-2 rounded-xl border border-border bg-card p-3 text-sm"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-base font-bold">{a.title}</h3>
        <span className="text-muted-foreground">
          {taipeiDate(a.due_at)} 截止
        </span>
      </div>
      <p>
        完成 {a.done}／{total}
        {a.late > 0 ? `・遲交 ${a.late}` : ""}
      </p>
      <Button
        variant="outline"
        className="self-start"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        還沒完成 {a.pending.length} 人
        <ChevronDown
          aria-hidden
          className={`size-4 ${open ? "rotate-180" : ""}`}
        />
      </Button>
      {open && (
        <div className="flex flex-col gap-2">
          {a.pending.length > 0 ? (
            <StudentRows rows={a.pending} />
          ) : (
            <p className="text-muted-foreground">全部都完成了。</p>
          )}
          {a.late_students.length > 0 && (
            <>
              <h4 className="font-bold">遲交</h4>
              <StudentRows rows={a.late_students} />
            </>
          )}
          {confirming ? (
            <div className="flex flex-wrap gap-2">
              <Button
                variant="destructive"
                disabled={remove.isPending}
                onClick={() => remove.mutate()}
              >
                確定刪除這份作業
              </Button>
              <Button variant="outline" onClick={() => setConfirming(false)}>
                取消
              </Button>
            </div>
          ) : (
            <Button
              variant="ghost"
              className="self-start text-muted-foreground"
              onClick={() => setConfirming(true)}
            >
              <Trash2 aria-hidden className="size-4" />
              刪除作業
            </Button>
          )}
        </div>
      )}
    </li>
  )
}
