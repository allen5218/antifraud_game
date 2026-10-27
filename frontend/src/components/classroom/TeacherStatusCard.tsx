import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { ChevronRight, GraduationCap } from "lucide-react"
import { useState } from "react"
import type { UserPublic } from "@/client"
import { UsersService } from "@/client/sdk.gen"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { HOME_SUMMARY_KEY } from "@/hooks/useHomeSummary"

/** 「我」頁的老師身分：申請、審核中、沒通過、已核准（進班級管理）、暫停 */
export function TeacherStatusCard({ user }: { user: UserPublic }) {
  const status = user.teacher_status ?? "none"
  const [open, setOpen] = useState(false)
  if (user.is_guest) return null
  if (status === "approved") {
    return (
      <Link
        to="/classes"
        className="flex items-center gap-3 rounded-xl border border-border bg-card px-3 py-3 text-sm transition hover:bg-accent"
      >
        <GraduationCap aria-hidden className="size-5 text-primary" />
        <span className="flex-1">班級管理</span>
        <ChevronRight aria-hidden className="size-4 text-muted-foreground" />
      </Link>
    )
  }
  return (
    <section className="rounded-xl border border-border bg-card p-3 text-sm">
      <h3 className="flex items-center gap-2 font-bold">
        <GraduationCap aria-hidden className="size-5 text-primary" />
        老師帳號
      </h3>
      {status === "none" && (
        <p className="mt-1 text-muted-foreground">
          老師可以建立班級、出作業，看全班哪一類詐騙最弱。申請後要管理員核准。
        </p>
      )}
      {status === "pending" && <p className="mt-1">老師身分審核中</p>}
      {status === "rejected" && (
        <p className="mt-1">老師身分申請沒有通過，可以補充資料再申請一次。</p>
      )}
      {status === "suspended" && (
        <p className="mt-1">老師身分已暫停，有問題請聯絡管理員。</p>
      )}
      {(status === "none" || status === "rejected") &&
        (open ? (
          <TeacherApplyForm onDone={() => setOpen(false)} />
        ) : (
          <Button
            variant="outline"
            className="mt-2"
            onClick={() => setOpen(true)}
          >
            {status === "none" ? "申請成為老師" : "再申請一次"}
          </Button>
        ))}
    </section>
  )
}

function TeacherApplyForm({ onDone }: { onDone: () => void }) {
  const queryClient = useQueryClient()
  const [school, setSchool] = useState("")
  const [subject, setSubject] = useState("")
  const apply = useMutation({
    mutationFn: () =>
      UsersService.applyTeacherMe({
        requestBody: { school: school.trim(), subject: subject.trim() },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      queryClient.invalidateQueries({ queryKey: HOME_SUMMARY_KEY })
      onDone()
    },
  })
  const ready = school.trim() !== "" && subject.trim() !== ""
  return (
    <form
      className="mt-2 flex flex-col gap-2"
      onSubmit={(event) => {
        event.preventDefault()
        if (ready && !apply.isPending) apply.mutate()
      }}
    >
      <label htmlFor="teacher-school" className="font-medium">
        學校
      </label>
      <Input
        id="teacher-school"
        value={school}
        maxLength={100}
        onChange={(event) => setSchool(event.target.value)}
      />
      <label htmlFor="teacher-subject" className="font-medium">
        任教科目
      </label>
      <Input
        id="teacher-subject"
        value={subject}
        maxLength={100}
        onChange={(event) => setSubject(event.target.value)}
      />
      {apply.isError && (
        <p role="alert" className="text-scam">
          送出失敗，請再試一次。
        </p>
      )}
      <Button type="submit" disabled={!ready || apply.isPending}>
        送出申請
      </Button>
    </form>
  )
}
