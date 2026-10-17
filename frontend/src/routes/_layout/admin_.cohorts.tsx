import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, redirect } from "@tanstack/react-router"
import { Download, QrCode, Users } from "lucide-react"
import { QRCodeCanvas } from "qrcode.react"
import { type FormEvent, useRef, useState } from "react"
import { AdminCohortsService, type CohortPublic, UsersService } from "@/client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export const Route = createFileRoute("/_layout/admin_/cohorts")({
  component: CohortsPage,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (!user.is_superuser) throw redirect({ to: "/" })
  },
  head: () => ({ meta: [{ title: "試測梯次 - ScamGym 識詐練習場" }] }),
})

function downloadFile(href: string, filename: string) {
  const link = document.createElement("a")
  link.href = href
  link.download = filename
  link.click()
}

function downloadCsv(data: string, filename: string) {
  const blob = new Blob(["\ufeff", data.replace(/^\ufeff/, "")], {
    type: "text/csv;charset=utf-8",
  })
  const url = URL.createObjectURL(blob)
  downloadFile(url, filename)
  // 保留到瀏覽器開始下載後再釋放。
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

function InvitationCode({ cohort }: { cohort: CohortPublic }) {
  const canvas = useRef<HTMLCanvasElement>(null)
  const url = `${window.location.origin}/invite/${cohort.token}`

  return (
    <div className="flex flex-col gap-3">
      {/* QR code 固定黑格白底：深色模式的反色碼很多手機掃不出來，這是只用主題色的例外 */}
      <div className="self-start rounded-xl bg-white p-3">
        <QRCodeCanvas
          ref={canvas}
          value={url}
          size={256}
          marginSize={2}
          bgColor="#ffffff"
          fgColor="#000000"
          title={`${cohort.name}的邀請碼`}
        />
      </div>
      <a href={url} className="break-all text-sm text-primary">
        {url}
      </a>
      <Button
        variant="outline"
        className="self-start"
        onClick={() => {
          if (canvas.current)
            downloadFile(
              canvas.current.toDataURL("image/png"),
              `invite-${cohort.id}.png`,
            )
        }}
      >
        <QrCode aria-hidden className="size-4" />
        下載邀請圖片
      </Button>
    </div>
  )
}

function CohortsPage() {
  const queryClient = useQueryClient()
  const [name, setName] = useState("")
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const cohorts = useQuery({
    queryKey: ["admin", "cohorts"],
    queryFn: () => AdminCohortsService.listCohorts(),
  })
  const selected = cohorts.data?.find((cohort) => cohort.id === selectedId)
  const members = useQuery({
    queryKey: ["admin", "cohorts", selectedId, "members"],
    queryFn: () => AdminCohortsService.listMembers({ cohortId: selectedId! }),
    enabled: Boolean(selectedId),
  })
  const create = useMutation({
    mutationFn: () =>
      AdminCohortsService.createCohort({ requestBody: { name: name.trim() } }),
    onSuccess: (cohort) => {
      setName("")
      setSelectedId(cohort.id)
      setNotice(null)
      queryClient.invalidateQueries({ queryKey: ["admin", "cohorts"] })
    },
    onError: () => setNotice("建立失敗，請稍後再試。"),
  })
  const toggle = useMutation({
    mutationFn: (cohort: CohortPublic) =>
      AdminCohortsService.updateCohort({
        cohortId: cohort.id,
        requestBody: { is_active: !cohort.is_active },
      }),
    onSuccess: () => {
      setNotice(null)
      queryClient.invalidateQueries({ queryKey: ["admin", "cohorts"] })
    },
    onError: () => setNotice("更新失敗，請稍後再試。"),
  })
  const exportCsv = useMutation({
    mutationFn: (cohortId: string) =>
      AdminCohortsService.exportCohort({ cohortId }),
    onSuccess: (data, cohortId) => {
      downloadCsv(data, `cohort-${cohortId}.csv`)
      setNotice(null)
    },
    onError: () => setNotice("下載失敗，請稍後再試。"),
  })
  const exportExamCsv = useMutation({
    mutationFn: (cohortId: string) =>
      AdminCohortsService.exportCohortExam({ cohortId }),
    onSuccess: (data, cohortId) => {
      downloadCsv(data, `cohort-${cohortId}-exam.csv`)
      setNotice(null)
    },
    onError: () => setNotice("下載失敗，請稍後再試。"),
  })
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (name.trim()) create.mutate()
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <Link to="/admin" className="text-sm text-primary">
          回到帳號管理
        </Link>
        <h1 className="mt-2 text-2xl font-bold">試測梯次</h1>
        <p className="text-muted-foreground">建立邀請碼，讓試測者掃碼加入。</p>
      </header>
      <form onSubmit={submit} className="flex flex-wrap items-end gap-3">
        <div className="flex-1">
          <label
            htmlFor="cohort-name"
            className="mb-2 block text-sm font-medium"
          >
            梯次名稱
          </label>
          <Input
            id="cohort-name"
            value={name}
            maxLength={100}
            required
            onChange={(event) => setName(event.target.value)}
            placeholder="例如：十月試測"
          />
        </div>
        <Button type="submit" disabled={!name.trim() || create.isPending}>
          建立梯次
        </Button>
      </form>
      {notice && (
        <p role="alert" className="text-scam">
          {notice}
        </p>
      )}
      {cohorts.isPending && <output>正在載入梯次…</output>}
      {cohorts.isError && (
        <p role="alert" className="text-scam">
          無法載入梯次。
          <Button variant="outline" onClick={() => cohorts.refetch()}>
            再試一次
          </Button>
        </p>
      )}
      {cohorts.data?.length === 0 && (
        <p className="text-muted-foreground">還沒有試測梯次。</p>
      )}
      <div className="grid gap-3 md:grid-cols-2">
        {cohorts.data?.map((cohort) => (
          <section
            key={cohort.id}
            className="rounded-xl border border-border bg-card p-4"
          >
            <h2 className="font-bold">{cohort.name}</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {cohort.is_active ? "開放加入" : "已停用"}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button
                variant="outline"
                onClick={() => setSelectedId(cohort.id)}
              >
                <Users aria-hidden className="size-4" />
                查看邀請與成員
              </Button>
              <Button
                variant="outline"
                disabled={toggle.isPending}
                onClick={() => toggle.mutate(cohort)}
              >
                {cohort.is_active ? "停用邀請" : "重新啟用"}
              </Button>
            </div>
          </section>
        ))}
      </div>
      {selected && (
        <section className="rounded-xl border border-border bg-surface-2 p-4">
          <h2 className="mb-4 text-lg font-bold">{selected.name}</h2>
          {!selected.is_active && (
            <p className="mb-3 text-warning">
              邀請已停用，既有成員仍可繼續練習。
            </p>
          )}
          <InvitationCode key={selected.id} cohort={selected} />
          <div className="mb-3 mt-6 flex flex-wrap items-center gap-3">
            <h3 className="flex-1 font-bold">
              成員（{members.data?.length ?? 0} 人）
            </h3>
            <Button variant="outline" onClick={() => members.refetch()}>
              更新成員
            </Button>
            <Button
              disabled={exportCsv.isPending}
              onClick={() => exportCsv.mutate(selected.id)}
            >
              <Download aria-hidden className="size-4" />
              下載作答資料
            </Button>
            <Button
              variant="outline"
              disabled={exportExamCsv.isPending}
              onClick={() => exportExamCsv.mutate(selected.id)}
            >
              <Download aria-hidden className="size-4" />
              下載檢測作答 CSV
            </Button>
          </div>
          {members.isPending && <output>正在載入成員…</output>}
          {members.isError && (
            <p role="alert" className="text-scam">
              無法載入成員，請再更新一次。
            </p>
          )}
          {members.data?.length === 0 && (
            <p className="text-muted-foreground">還沒有人加入。</p>
          )}
          {members.data && members.data.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="p-2">受試編號</th>
                    <th className="p-2">暱稱</th>
                    <th className="p-2">加入時間</th>
                    <th className="p-2">作答題數</th>
                    <th className="p-2">答對題數</th>
                  </tr>
                </thead>
                <tbody>
                  {members.data.map((member) => (
                    <tr key={member.id} className="border-b border-border">
                      <td className="p-2">{member.participant_code}</td>
                      <td className="p-2">{member.nickname || "尚未設定"}</td>
                      <td className="p-2">
                        {member.created_at
                          ? new Date(member.created_at).toLocaleString(
                              "zh-TW",
                              { timeZone: "Asia/Taipei" },
                            )
                          : "尚無資料"}
                      </td>
                      <td className="p-2">{member.answer_count}</td>
                      <td className="p-2">{member.correct_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </div>
  )
}
