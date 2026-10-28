import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, redirect } from "@tanstack/react-router"
import { BarChart3, Download, GraduationCap, QrCode, Users } from "lucide-react"
import { QRCodeCanvas } from "qrcode.react"
import { type FormEvent, useRef, useState } from "react"
import {
  AdminCohortsService,
  type CohortProgressMember,
  type CohortPublic,
  UsersService,
} from "@/client"
import { TeacherAdmin } from "@/components/classroom/TeacherAdmin"
import { CohortSettings } from "@/components/trialAdmin/CohortSettings"
import { expiryOf, limitText } from "@/components/trialAdmin/format"
import { MemberDetail } from "@/components/trialAdmin/MemberDetail"
import { ProgressTable } from "@/components/trialAdmin/ProgressTable"
import { TrialAnalytics } from "@/components/trialAdmin/TrialAnalytics"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { downloadCsv, downloadFile } from "@/lib/download"

export const Route = createFileRoute("/_layout/admin_/cohorts")({
  component: CohortsPage,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (!user.is_superuser) throw redirect({ to: "/" })
  },
  head: () => ({ meta: [{ title: "試測梯次 - ScamGym 識詐練習場" }] }),
})

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
  const [quota, setQuota] = useState("")
  const [lastDay, setLastDay] = useState("")
  const [view, setView] = useState<"cohorts" | "analytics" | "teachers">(
    "cohorts",
  )
  const [member, setMember] = useState<CohortProgressMember | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const cohorts = useQuery({
    queryKey: ["admin", "cohorts"],
    queryFn: () => AdminCohortsService.listCohorts(),
  })
  const selected = cohorts.data?.find((cohort) => cohort.id === selectedId)
  const progress = useQuery({
    queryKey: ["admin", "cohorts", selectedId, "progress"],
    queryFn: () =>
      AdminCohortsService.cohortProgress({ cohortId: selectedId! }),
    enabled: Boolean(selectedId),
  })
  const create = useMutation({
    mutationFn: () =>
      AdminCohortsService.createCohort({
        requestBody: {
          name: name.trim(),
          ...(quota.trim() ? { max_members: Number(quota) } : {}),
          ...(lastDay ? { expires_at: expiryOf(lastDay) } : {}),
        },
      }),
    onSuccess: (cohort) => {
      setName("")
      setQuota("")
      setLastDay("")
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
  const exportSurveyCsv = useMutation({
    mutationFn: (cohortId: string) =>
      AdminCohortsService.exportCohortSurvey({ cohortId }),
    onSuccess: (data, cohortId) => {
      downloadCsv(data, `cohort-${cohortId}-survey.csv`)
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
        <div className="flex gap-4 text-sm">
          <Link to="/" className="text-primary">
            回房間
          </Link>
          <Link to="/admin" className="text-primary">
            回到帳號管理
          </Link>
        </div>
        <h1 className="mt-2 text-2xl font-bold">試測梯次</h1>
        <p className="text-muted-foreground">
          開新的一輪梯次、發邀請網址與 QR
          code，看每個人做到哪裡、能不能領錢，以及試測數據與問卷分析。名稱、名額和期限隨時可以改。
        </p>
        <div
          className="mt-3 flex flex-wrap gap-2"
          role="tablist"
          aria-label="管理頁"
        >
          {(
            [
              ["cohorts", Users, "梯次與成員"],
              ["analytics", BarChart3, "數據分析"],
              ["teachers", GraduationCap, "老師管理"],
            ] as const
          ).map(([key, Icon, label]) => (
            <Button
              key={key}
              role="tab"
              aria-selected={view === key}
              variant={view === key ? "default" : "outline"}
              onClick={() => setView(key)}
            >
              <Icon aria-hidden className="size-4" />
              {label}
            </Button>
          ))}
        </div>
      </header>
      {view === "analytics" && <TrialAnalytics cohorts={cohorts.data ?? []} />}
      {view === "teachers" && <TeacherAdmin />}
      {view === "cohorts" && (
        <>
          <form onSubmit={submit} className="flex flex-wrap items-end gap-3">
            <div className="basis-full sm:flex-1 sm:basis-auto">
              <label
                htmlFor="cohort-name"
                className="mb-2 block text-sm font-medium"
              >
                新梯次名稱
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
            <div>
              <label
                htmlFor="new-cohort-quota"
                className="mb-2 block text-sm font-medium"
              >
                新梯次名額（留空是不限）
              </label>
              <Input
                id="new-cohort-quota"
                type="number"
                min={1}
                max={5000}
                inputMode="numeric"
                value={quota}
                onChange={(event) => setQuota(event.target.value)}
                placeholder="不限"
                className="w-32"
              />
            </div>
            <div>
              <label
                htmlFor="new-cohort-expiry"
                className="mb-2 block text-sm font-medium"
              >
                新梯次最後一天（留空是不限期限）
              </label>
              <Input
                id="new-cohort-expiry"
                type="date"
                value={lastDay}
                onChange={(event) => setLastDay(event.target.value)}
                className="w-44"
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
                <p className="mt-1 text-sm text-muted-foreground">
                  {limitText(cohort)}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setSelectedId(cohort.id)
                      setMember(null)
                    }}
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
              <CohortSettings
                key={`settings-${selected.id}`}
                cohort={selected}
              />
              <div className="mb-3 mt-6 flex flex-wrap items-center gap-3">
                <h3 className="flex-1 font-bold">
                  試測進度（{progress.data?.member_count ?? 0} 人）
                </h3>
                <Button
                  variant="outline"
                  onClick={() => {
                    progress.refetch()
                    cohorts.refetch()
                  }}
                >
                  更新
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
                <Button
                  variant="outline"
                  disabled={exportSurveyCsv.isPending}
                  onClick={() => exportSurveyCsv.mutate(selected.id)}
                >
                  <Download aria-hidden className="size-4" />
                  下載問卷 CSV
                </Button>
              </div>
              {progress.isPending && <output>正在載入試測進度…</output>}
              {progress.isError && (
                <p role="alert" className="text-scam">
                  無法載入試測進度，請再更新一次。
                </p>
              )}
              {progress.data && (
                <ProgressTable progress={progress.data} onOpen={setMember} />
              )}
              <MemberDetail
                cohortId={selected.id}
                userId={member?.user_id ?? null}
                code={member?.participant_code ?? null}
                onClose={() => setMember(null)}
              />
            </section>
          )}
        </>
      )}
    </div>
  )
}
