import { useQuery } from "@tanstack/react-query"
import type { ClassMemberPublic } from "@/client"
import {
  EXAM_MODE_LABELS,
  EXAM_STATUS_LABELS,
  PRACTICE_MODE_LABELS,
  taipeiTime,
} from "@/components/trialAdmin/format"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { fraudTypeLabel } from "@/lib/fraudTypes"
import { classApi } from "./classroomApi"
import { STATUS_LABELS, studentLabel } from "./format"

/** 學生詳情：每份作業的狀態、每次檢測、三種練習量 */
export function StudentDetail({
  classId,
  member,
  onClose,
}: {
  classId: string
  member: ClassMemberPublic
  onClose: () => void
}) {
  const detail = useQuery({
    queryKey: ["classes", classId, "member", member.user_id],
    queryFn: () => classApi.member(classId, member.user_id),
  })
  const d = detail.data
  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[90dvh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{studentLabel(member)}</DialogTitle>
        </DialogHeader>
        {detail.isPending && <output>正在載入…</output>}
        {detail.isError && (
          <p role="alert" className="text-scam">
            讀不到資料，請再試一次。
          </p>
        )}
        {d && (
          <div className="flex flex-col gap-4 text-sm">
            <p className="text-muted-foreground">
              加入 {taipeiTime(d.joined_at)}・最後上線{" "}
              {taipeiTime(d.last_active_at)}
            </p>
            <section>
              <h3 className="font-bold">作業</h3>
              {d.assignments.length === 0 ? (
                <p className="text-muted-foreground">
                  還沒有作業，或學生還沒填學號名字。
                </p>
              ) : (
                <ul className="divide-y divide-border">
                  {d.assignments.map((a) => (
                    <li key={a.id} className="flex justify-between gap-2 py-1">
                      <span>{a.title}</span>
                      <span className="text-muted-foreground">
                        {STATUS_LABELS[a.status] ?? a.status}
                        {(a.status === "todo" || a.status === "overdue") &&
                        a.progress_text !== STATUS_LABELS.todo
                          ? `・${a.progress_text}`
                          : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
            <section>
              <h3 className="font-bold">檢測</h3>
              {d.exams.length === 0 ? (
                <p className="text-muted-foreground">還沒考過。</p>
              ) : (
                <ul className="divide-y divide-border">
                  {d.exams.map((e) => (
                    <li key={e.id} className="flex flex-col py-1">
                      <span>
                        {EXAM_MODE_LABELS[e.mode] ?? e.mode}
                        {e.fraud_type
                          ? `・${fraudTypeLabel(e.fraud_type)}`
                          : ""}
                        ・{EXAM_STATUS_LABELS[e.status] ?? e.status}・{e.score}{" "}
                        分
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {taipeiTime(e.completed_at ?? e.started_at)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
            <section>
              <h3 className="font-bold">練習</h3>
              <p>
                {d.practice
                  .map(
                    (p) =>
                      `${PRACTICE_MODE_LABELS[p.mode] ?? p.mode} ${p.total}（對 ${p.correct}）`,
                  )
                  .join("・")}
              </p>
            </section>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
