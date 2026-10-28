import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import type { ClassMemberPublic } from "@/client"
import { taipeiTime } from "@/components/trialAdmin/format"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { classApi } from "./classroomApi"
import { studentLabel } from "./format"

/** 學生名單：手機一人一張卡片、桌機表格；改學號名字與移出都用對話框確認 */
export function RosterTable({
  classId,
  members,
  onOpen,
}: {
  classId: string
  members: ClassMemberPublic[]
  onOpen: (member: ClassMemberPublic) => void
}) {
  const [removing, setRemoving] = useState<ClassMemberPublic | null>(null)
  const [editing, setEditing] = useState<ClassMemberPublic | null>(null)
  if (members.length === 0)
    return (
      <p className="text-muted-foreground">
        還沒有學生加入。把下面的 QR code 或班級代碼給學生。
      </p>
    )
  const actions = (m: ClassMemberPublic) => (
    <div className="flex flex-wrap gap-1">
      <Button size="sm" variant="outline" onClick={() => onOpen(m)}>
        詳情
      </Button>
      <Button size="sm" variant="outline" onClick={() => setEditing(m)}>
        改學號名字
      </Button>
      <Button size="sm" variant="ghost" onClick={() => setRemoving(m)}>
        移出
      </Button>
    </div>
  )
  return (
    <>
      <ul className="flex flex-col gap-2 md:hidden">
        {members.map((m) => (
          <li
            key={m.user_id}
            className="flex flex-col gap-1 rounded-lg border border-border bg-card p-3 text-sm"
          >
            <span className="font-bold">{studentLabel(m)}</span>
            <span className="text-muted-foreground">
              最近檢測 {m.latest_exam_score ?? "—"} 分・最後上線{" "}
              {taipeiTime(m.last_active_at)}
            </span>
            {actions(m)}
          </li>
        ))}
      </ul>
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="whitespace-nowrap p-2">學號</th>
              <th className="whitespace-nowrap p-2">名字</th>
              <th className="whitespace-nowrap p-2">最近檢測</th>
              <th className="whitespace-nowrap p-2">最後上線</th>
              <th className="p-2" />
            </tr>
          </thead>
          <tbody>
            {members.map((m) => (
              <tr key={m.user_id} className="border-b border-border">
                <td className="p-2">{m.student_number ?? "還沒填"}</td>
                <td className="p-2">{m.student_name ?? "還沒填"}</td>
                <td className="p-2">{m.latest_exam_score ?? "—"}</td>
                <td className="whitespace-nowrap p-2">
                  {taipeiTime(m.last_active_at)}
                </td>
                <td className="p-2">{actions(m)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {removing && (
        <RemoveDialog
          classId={classId}
          member={removing}
          onClose={() => setRemoving(null)}
        />
      )}
      {editing && (
        <EditDialog
          classId={classId}
          member={editing}
          onClose={() => setEditing(null)}
        />
      )}
    </>
  )
}

function RemoveDialog({
  classId,
  member,
  onClose,
}: {
  classId: string
  member: ClassMemberPublic
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const remove = useMutation({
    mutationFn: () => classApi.removeMember(classId, member.user_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["classes"] })
      onClose()
    },
  })
  const label = studentLabel(member)
  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>要把 {label} 移出班級嗎？</DialogTitle>
          <DialogDescription>
            移出後他看不到這個班的作業；他的練習與檢測紀錄不會刪除。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button
            variant="destructive"
            aria-label={`確定移出${member.student_name ?? label}`}
            disabled={remove.isPending}
            onClick={() => remove.mutate()}
          >
            確定移出
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function EditDialog({
  classId,
  member,
  onClose,
}: {
  classId: string
  member: ClassMemberPublic
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const [number, setNumber] = useState(member.student_number ?? "")
  const [name, setName] = useState(member.student_name ?? "")
  const save = useMutation({
    mutationFn: () =>
      classApi.updateMember(classId, member.user_id, {
        student_number: number.trim(),
        student_name: name.trim(),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["classes"] })
      onClose()
    },
  })
  const ready = number.trim() !== "" && name.trim() !== ""
  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>改學號名字</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-1 text-sm">
          <label htmlFor="member-number" className="font-medium">
            學號
          </label>
          <Input
            id="member-number"
            value={number}
            maxLength={32}
            onChange={(event) => setNumber(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1 text-sm">
          <label htmlFor="member-name" className="font-medium">
            名字
          </label>
          <Input
            id="member-name"
            value={name}
            maxLength={50}
            onChange={(event) => setName(event.target.value)}
          />
        </div>
        {save.isError && (
          <p role="alert" className="text-sm text-scam">
            儲存失敗，請再試一次。
          </p>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button
            disabled={!ready || save.isPending}
            onClick={() => save.mutate()}
          >
            儲存
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
