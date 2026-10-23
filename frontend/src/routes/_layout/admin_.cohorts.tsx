import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, redirect } from "@tanstack/react-router"
import { Download, QrCode, Users } from "lucide-react"
import { QRCodeCanvas } from "qrcode.react"
import { type FormEvent, useRef, useState } from "react"
import {
  AdminCohortsService,
  type CohortProgress,
  type CohortProgressMember,
  type CohortPublic,
  UsersService,
} from "@/client"
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

const TAIPEI = "Asia/Taipei"

/** 到期時間顯示成台灣日期，例如 2026/11/2 */
function taipeiDate(iso: string): string {
  return new Date(iso).toLocaleDateString("zh-TW", { timeZone: TAIPEI })
}

/** 日期欄位的值（YYYY-MM-DD，台灣時間） */
function dateInputValue(iso: string | null | undefined): string {
  if (!iso) return ""
  return new Date(iso).toLocaleDateString("sv-SE", { timeZone: TAIPEI })
}

/** 選的那天的台灣時間 23:59:59 到期 */
function expiryOf(date: string): string {
  return `${date}T23:59:59+08:00`
}

function limitText(cohort: CohortPublic): string {
  const quota =
    cohort.max_members == null ? "名額不限" : `名額 ${cohort.max_members} 人`
  const expiry = cohort.expires_at
    ? `${taipeiDate(cohort.expires_at)} 到期`
    : "不限期限"
  return `已加入 ${cohort.member_count ?? 0} 人・${quota}・${expiry}`
}

/** 名額與期限：留空是不限。改了馬上生效，已經加入的人不受影響 */
function CohortSettings({ cohort }: { cohort: CohortPublic }) {
  const queryClient = useQueryClient()
  const [quota, setQuota] = useState(
    cohort.max_members == null ? "" : String(cohort.max_members),
  )
  const [date, setDate] = useState(dateInputValue(cohort.expires_at))
  const [message, setMessage] = useState<string | null>(null)
  const save = useMutation({
    mutationFn: () =>
      AdminCohortsService.updateCohort({
        cohortId: cohort.id,
        requestBody: {
          max_members: quota.trim() ? Number(quota) : null,
          expires_at: date ? expiryOf(date) : null,
        },
      }),
    onSuccess: () => {
      setMessage("已儲存。")
      queryClient.invalidateQueries({ queryKey: ["admin", "cohorts"] })
    },
    onError: () => setMessage("儲存失敗，名額要是 1 到 5000 的整數。"),
  })
  return (
    <form
      className="mt-6 flex flex-wrap items-end gap-3"
      onSubmit={(event) => {
        event.preventDefault()
        save.mutate()
      }}
    >
      <div>
        <label
          htmlFor="cohort-quota"
          className="mb-1 block text-sm font-medium"
        >
          名額（留空是不限）
        </label>
        <Input
          id="cohort-quota"
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
          htmlFor="cohort-expiry"
          className="mb-1 block text-sm font-medium"
        >
          最後一天（留空是不限期限）
        </label>
        <Input
          id="cohort-expiry"
          type="date"
          value={date}
          onChange={(event) => setDate(event.target.value)}
          className="w-44"
        />
      </div>
      <Button type="submit" variant="outline" disabled={save.isPending}>
        儲存設定
      </Button>
      {message && (
        <output className="text-sm text-muted-foreground">{message}</output>
      )}
    </form>
  )
}

function seconds(value: number | null | undefined): string {
  if (value == null) return "沒有計時"
  if (value < 60) return `${value} 秒`
  return `${Math.floor(value / 60)} 分 ${value % 60} 秒`
}

function pretestText(m: CohortProgressMember): string {
  return m.pretest_done
    ? `答對 ${m.pretest_correct}／${m.pretest_total}・${seconds(m.pretest_seconds)}`
    : "沒做"
}

function examText(m: CohortProgressMember): string {
  return m.exam_completed
    ? `${m.best_exam_score} 分・最久 ${seconds(m.exam_seconds)}`
    : "沒交卷"
}

function surveyText(m: CohortProgressMember): string {
  return m.survey_done
    ? `${seconds(m.survey_seconds)}・注意力題${m.survey_attention_ok ? "對" : "錯"}`
    : "沒填"
}

/** 每個人的前測、檢測、問卷與能不能領錢（和「下載作答資料」同一套判定） */
function ProgressTable({ progress }: { progress: CohortProgress }) {
  const stats = [
    ["已加入", progress.member_count],
    ["前測做完", progress.pretest_done],
    ["檢測交卷", progress.exam_completed],
    ["問卷交了", progress.survey_done],
    ["可以領錢", progress.payout_eligible],
  ] as const
  return (
    <div className="flex flex-col gap-3">
      <dl className="grid grid-cols-5 gap-2">
        {stats.map(([label, value]) => (
          <div
            key={label}
            className="rounded-lg border border-border bg-card p-2 text-center"
          >
            <dt className="whitespace-nowrap text-[11px] text-muted-foreground">
              {label}
            </dt>
            <dd className="text-xl font-bold">{value}</dd>
          </div>
        ))}
      </dl>
      {progress.members.length === 0 ? (
        <p className="text-muted-foreground">還沒有人加入。</p>
      ) : (
        <>
          {/* 手機：一人一張卡片 */}
          <ul className="flex flex-col gap-2 md:hidden">
            {progress.members.map((m) => (
              <li
                key={m.participant_code ?? m.created_at}
                className="rounded-lg border border-border bg-card p-3 text-sm"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold">{m.participant_code}</span>
                  <span
                    className={`font-bold ${m.payout_eligible ? "text-legit" : "text-muted-foreground"}`}
                  >
                    {m.payout_eligible ? "可以領錢" : "還不能領"}
                  </span>
                </div>
                <p>前測：{pretestText(m)}</p>
                <p>檢測：{examText(m)}</p>
                <p>問卷：{surveyText(m)}</p>
                {m.payout_reasons.length > 0 && (
                  <p className="text-muted-foreground">
                    原因：{m.payout_reasons.join("、")}
                  </p>
                )}
              </li>
            ))}
          </ul>
          <div className="hidden overflow-x-auto md:block">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="whitespace-nowrap p-2">受試編號</th>
                  <th className="whitespace-nowrap p-2">加入時間</th>
                  <th className="whitespace-nowrap p-2">前測</th>
                  <th className="whitespace-nowrap p-2">檢測</th>
                  <th className="whitespace-nowrap p-2">問卷</th>
                  <th className="whitespace-nowrap p-2">可以領錢</th>
                  <th className="whitespace-nowrap p-2">不能領的原因</th>
                </tr>
              </thead>
              <tbody>
                {progress.members.map((m) => (
                  <tr
                    key={m.participant_code ?? m.created_at}
                    className="border-b border-border align-top"
                  >
                    <td className="whitespace-nowrap p-2 font-medium">
                      {m.participant_code}
                    </td>
                    <td className="p-2 whitespace-nowrap">
                      {m.created_at
                        ? new Date(m.created_at).toLocaleString("zh-TW", {
                            timeZone: TAIPEI,
                          })
                        : "尚無資料"}
                    </td>
                    <td className="p-2">{pretestText(m)}</td>
                    <td className="p-2">{examText(m)}</td>
                    <td className="p-2">{surveyText(m)}</td>
                    <td
                      className={`whitespace-nowrap p-2 font-bold ${m.payout_eligible ? "text-legit" : "text-muted-foreground"}`}
                    >
                      {m.payout_eligible ? "可以" : "還不行"}
                    </td>
                    <td className="p-2 text-muted-foreground">
                      {m.payout_reasons.join("、")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}

function CohortsPage() {
  const queryClient = useQueryClient()
  const [name, setName] = useState("")
  const [quota, setQuota] = useState("")
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
        },
      }),
    onSuccess: (cohort) => {
      setName("")
      setQuota("")
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
          建立邀請網址與 QR
          code，看每個人做到哪裡、能不能領錢。名額和期限隨時可以改。
        </p>
      </header>
      <form onSubmit={submit} className="flex flex-wrap items-end gap-3">
        <div className="basis-full sm:flex-1 sm:basis-auto">
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
        <div>
          <label
            htmlFor="new-cohort-quota"
            className="mb-2 block text-sm font-medium"
          >
            名額（留空是不限）
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
          <CohortSettings key={`settings-${selected.id}`} cohort={selected} />
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
          {progress.data && <ProgressTable progress={progress.data} />}
        </section>
      )}
    </div>
  )
}
