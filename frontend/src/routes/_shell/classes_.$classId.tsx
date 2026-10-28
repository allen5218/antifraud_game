import { useMutation, useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { Download } from "lucide-react"
import { useState } from "react"
import type { ClassMemberPublic } from "@/client"
import { AssignmentForm } from "@/components/classroom/AssignmentForm"
import { AssignmentList } from "@/components/classroom/AssignmentList"
import { ClassInvite } from "@/components/classroom/ClassInvite"
import { CLASSES_KEY } from "@/components/classroom/ClassList"
import { ClassOverviewCard } from "@/components/classroom/ClassOverviewCard"
import { classApi } from "@/components/classroom/classroomApi"
import { RosterTable } from "@/components/classroom/RosterTable"
import { StudentDetail } from "@/components/classroom/StudentDetail"
import { Button } from "@/components/ui/button"
import { downloadCsv } from "@/lib/download"

export const Route = createFileRoute("/_shell/classes_/$classId")({
  component: ClassPage,
  head: () => ({ meta: [{ title: "班級 - ScamGym 識詐練習場" }] }),
})

const SECTION =
  "flex flex-col gap-3 rounded-2xl border border-border bg-card p-4"

function ClassPage() {
  const { classId } = Route.useParams()
  const [adding, setAdding] = useState(false)
  const [member, setMember] = useState<ClassMemberPublic | null>(null)
  const classes = useQuery({ queryKey: CLASSES_KEY, queryFn: classApi.list })
  const overview = useQuery({
    queryKey: ["classes", classId, "overview"],
    queryFn: () => classApi.overview(classId),
  })
  const members = useQuery({
    queryKey: ["classes", classId, "members"],
    queryFn: () => classApi.members(classId),
  })
  const exportCsv = useMutation({
    mutationFn: () => classApi.exportCsv(classId),
    onSuccess: (data) => downloadCsv(data, `class-${classId}.csv`),
  })
  const classroom = classes.data?.find((c) => c.id === classId)
  if (classes.isSuccess && !classroom)
    return (
      <p className="py-12 text-center text-muted-foreground">
        找不到這個班級。 <Link to="/classes">回班級管理</Link>
      </p>
    )
  return (
    <div className="flex flex-col gap-4 pb-8">
      <header className="flex flex-col gap-1">
        <Link to="/classes" className="text-sm text-primary">
          回班級管理
        </Link>
        <h1 className="text-2xl font-bold">{classroom?.name ?? "載入中…"}</h1>
        {overview.data && (
          <p className="text-sm text-muted-foreground">
            {overview.data.member_count} 位學生
          </p>
        )}
      </header>
      {overview.isError && (
        <p role="alert" className="text-scam">
          讀不到班級資料，請重新整理。
        </p>
      )}
      {overview.data && <ClassOverviewCard data={overview.data} />}
      <section className={SECTION}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-bold">作業</h2>
          <Button variant="outline" onClick={() => setAdding(!adding)}>
            {adding ? "收起" : "新增作業"}
          </Button>
        </div>
        {adding && (
          <AssignmentForm classId={classId} onDone={() => setAdding(false)} />
        )}
        {overview.data && (
          <AssignmentList classId={classId} data={overview.data} />
        )}
      </section>
      <section className={SECTION}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-bold">學生名單</h2>
          <Button
            variant="outline"
            disabled={exportCsv.isPending}
            onClick={() => exportCsv.mutate()}
          >
            <Download aria-hidden className="size-4" />
            下載 CSV
          </Button>
        </div>
        {members.data && (
          <RosterTable
            classId={classId}
            members={members.data}
            onOpen={setMember}
          />
        )}
      </section>
      {classroom && (
        <section className={SECTION}>
          <h2 className="text-lg font-bold">邀請學生</h2>
          <ClassInvite key={classroom.name} classroom={classroom} />
        </section>
      )}
      {member && (
        <StudentDetail
          classId={classId}
          member={member}
          onClose={() => setMember(null)}
        />
      )}
    </div>
  )
}
