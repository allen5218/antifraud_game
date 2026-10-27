import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import type { TeacherPublic } from "@/client"
import { AdminTeachersService } from "@/client/sdk.gen"
import { taipeiTime } from "@/components/trialAdmin/format"
import { Button } from "@/components/ui/button"

type Status = "pending" | "approved" | "suspended" | "rejected"
type Action = "approve" | "reject" | "suspend" | "restore"

const FILTERS: [Status, string][] = [
  ["pending", "審核中"],
  ["approved", "已核准"],
  ["suspended", "已停權"],
  ["rejected", "沒有通過"],
]

const ACTIONS: Record<Status, [Action, string, "default" | "outline"][]> = {
  pending: [
    ["approve", "核准", "default"],
    ["reject", "拒絕", "outline"],
  ],
  approved: [["suspend", "停權", "outline"]],
  suspended: [["restore", "恢復", "default"]],
  rejected: [],
}

/** 管理員的老師管理：手機上一人一張卡片，按鈕夠大 */
export function TeacherAdmin() {
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<Status>("pending")
  const teachers = useQuery({
    queryKey: ["admin", "teachers", status],
    queryFn: () => AdminTeachersService.listTeachers({ status }),
  })
  const change = useMutation({
    mutationFn: ({ userId, action }: { userId: string; action: Action }) =>
      AdminTeachersService.changeTeacher({ userId, action }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["admin", "teachers"] }),
  })
  return (
    <div className="flex flex-col gap-3">
      <div
        className="flex flex-wrap gap-2"
        role="tablist"
        aria-label="老師狀態"
      >
        {FILTERS.map(([key, label]) => (
          <Button
            key={key}
            role="tab"
            aria-selected={status === key}
            variant={status === key ? "default" : "outline"}
            onClick={() => setStatus(key)}
          >
            {label}
          </Button>
        ))}
      </div>
      {teachers.isPending && <output>正在載入…</output>}
      {teachers.isError && (
        <p role="alert" className="text-scam">
          讀不到老師名單，請再試一次。
        </p>
      )}
      {teachers.data?.length === 0 && (
        <p className="text-muted-foreground">這裡沒有人。</p>
      )}
      {change.isError && (
        <p role="alert" className="text-scam">
          更新失敗，請重新整理再試一次。
        </p>
      )}
      <ul className="grid gap-2 md:grid-cols-2">
        {teachers.data?.map((t) => (
          <TeacherCard
            key={t.id}
            teacher={t}
            actions={ACTIONS[status]}
            busy={change.isPending}
            onAction={(action) => change.mutate({ userId: t.id, action })}
          />
        ))}
      </ul>
    </div>
  )
}

function TeacherCard({
  teacher,
  actions,
  busy,
  onAction,
}: {
  teacher: TeacherPublic
  actions: [Action, string, "default" | "outline"][]
  busy: boolean
  onAction: (action: Action) => void
}) {
  return (
    <li className="flex flex-col gap-1 rounded-xl border border-border bg-card p-3 text-sm">
      <p className="text-base font-bold">
        {teacher.full_name || "（沒有名字）"}
      </p>
      <p className="break-all text-muted-foreground">{teacher.email}</p>
      <p>
        {teacher.school ?? "—"}・{teacher.subject ?? "—"}
      </p>
      <p className="text-xs text-muted-foreground">
        申請時間 {taipeiTime(teacher.applied_at)}・{teacher.class_count} 個班・
        {teacher.student_count} 位學生
      </p>
      {actions.length > 0 && (
        <div className="mt-2 flex gap-2">
          {actions.map(([action, label, variant]) => (
            <Button
              key={action}
              variant={variant}
              className="flex-1"
              disabled={busy}
              onClick={() => onAction(action)}
            >
              {label}
            </Button>
          ))}
        </div>
      )}
    </li>
  )
}
