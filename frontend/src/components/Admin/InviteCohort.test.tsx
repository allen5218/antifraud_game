/** 邀請與梯次管理的 DOM 測試。
 * 在 frontend 執行：bun test src/components/Admin/InviteCohort.test.tsx
 * QR 畫布與下載出口使用替身，實際掃碼與瀏覽器下載需另做驗證。
 */
import { afterEach, expect, mock, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react"
import React from "react"
import { ApiError } from "@/client/core/ApiError"

let token = "first"
let calls = 0
let mode = "success"
let cohorts: any[] = []
let createBody: unknown
let toggleBody: unknown
let analyticsScope: string | undefined = "unset"
let qrValue: string
const downloads: { href: string; filename: string }[] = []
const navigate = mock(async () => {})
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
})
const cohort = {
  id: "cohort-one",
  name: "第一梯",
  token: "invitation-token",
  is_active: true,
  max_members: 60,
  expires_at: "2026-11-02T15:59:59Z",
  member_count: 1,
  created_at: new Date().toISOString(),
  created_by: "admin",
}

const { QRCodeSVG } = await import("qrcode.react")

mock.module("@tanstack/react-router", () => ({
  createFileRoute: () => (options: any) => ({
    options,
    useParams: () => ({ token }),
  }),
  useNavigate: () => navigate,
  redirect: (options: unknown) => options,
  Link: ({ to, params, children, ...props }: any) => {
    let href = typeof to === "string" ? to : ""
    if (params && typeof params === "object") {
      for (const [key, value] of Object.entries(params)) {
        href = href.replaceAll(`$${key}`, String(value))
      }
    }
    return (
      <a {...props} href={href}>
        {children}
      </a>
    )
  },
}))
mock.module("qrcode.react", () => ({
  QRCodeSVG,
  QRCodeCanvas: ({ value, ref, title }: any) => {
    qrValue = value
    return (
      <canvas
        title={title}
        ref={(node) => {
          if (node) node.toDataURL = () => "data:image/png;base64,TEST"
          if (ref) ref.current = node
        }}
      />
    )
  },
}))
mock.module("@/client", () => ({
  ApiError,
  InviteService: {
    redeemInvite: async () => {
      calls++
      await new Promise((resolve) => setTimeout(resolve, 5))
      if (mode === "failure" || mode === "limited") {
        const status = mode === "limited" ? 429 : 404
        throw new ApiError(
          { method: "POST", url: "/invite" },
          { url: "/invite", ok: false, status, statusText: "Failed", body: {} },
          "Failed",
        )
      }
      return { access_token: `access-${token}`, token_type: "bearer" }
    },
  },
  UsersService: { readUserMe: async () => ({ is_superuser: true }) },
  AdminCohortsService: {
    listCohorts: async () => [...cohorts],
    createCohort: async ({ requestBody }: any) => {
      createBody = requestBody
      cohorts = [{ ...cohort, name: requestBody.name }]
      return cohorts[0]
    },
    cohortProgress: async () => ({
      member_count: 1,
      pretest_done: 1,
      exam_completed: 0,
      survey_done: 0,
      payout_eligible: 0,
      members: [
        {
          user_id: "user-one",
          participant_code: "T-0001",
          created_at: null,
          pretest_done: true,
          pretest_correct: 12,
          pretest_total: 20,
          pretest_seconds: 95,
          exam_completed: false,
          best_exam_score: null,
          exam_seconds: null,
          survey_done: false,
          survey_seconds: null,
          survey_attention_ok: null,
          payout_eligible: false,
          payout_reasons: ["檢測沒有交卷", "問卷沒填"],
        },
      ],
    }),
    updateCohort: async ({ requestBody }: any) => {
      toggleBody = requestBody
      cohorts = [{ ...cohorts[0], ...requestBody }]
      return cohorts[0]
    },
    memberDetail: async ({ userId }: { userId: string }) => {
      expect(userId).toBe("user-one")
      return {
        user_id: "user-one",
        participant_code: "T-0001",
        nickname: null,
        created_at: null,
        last_active_at: null,
        pretests: [
          {
            at: null,
            seconds: 95,
            correct: 1,
            total: 1,
            weakest_type: "atm",
            items: [
              {
                fraud_type: "atm",
                question: "客服來電說要解除分期",
                selected: "A",
                correct_option: "A",
                is_correct: true,
              },
            ],
          },
        ],
        exams: [],
        practice: [
          { mode: "swipe", total: 6, correct: 5 },
          { mode: "quiz", total: 0, correct: 0 },
          { mode: "scenario", total: 1, correct: 1 },
        ],
        scenario_sessions: 2,
        survey: null,
      }
    },
    analytics: async ({ cohortId }: { cohortId?: string }) => {
      analyticsScope = cohortId
      return {
        member_count: 1,
        funnel: [
          { key: "joined", label: "加入", count: 1 },
          { key: "exam", label: "檢測交卷", count: 0 },
        ],
        type_accuracy: [],
        scores: { n: 0, passed: 0, mean: null, bins: [] },
        timings: [],
        survey: {
          responses: 0,
          likert: [],
          confidence: {
            n: 0,
            before_mean: null,
            after_mean: null,
            diff_mean: null,
            improved: 0,
            same: 0,
            worse: 0,
          },
          choices: [],
          texts: [],
        },
      }
    },
    exportCohort: async () =>
      "\ufeffparticipant_code,answer_count\r\nT-0001,3\r\n",
    exportCohortExam: async ({ cohortId }: { cohortId: string }) => {
      expect(cohortId).toBe("cohort-one")
      return "\ufeffparticipant_code,correct\r\nT-0001,true\r\n"
    },
    exportCohortSurvey: async ({ cohortId }: { cohortId: string }) => {
      expect(cohortId).toBe("cohort-one")
      return "\ufeffparticipant_code,satisfied\r\nT-0001,4\r\n"
    },
  },
}))
HTMLAnchorElement.prototype.click = function () {
  downloads.push({ href: this.href, filename: this.download })
}

const { Route: InviteRoute } = await import("@/routes/invite.$token")
const { Route: AdminRoute } = await import("@/routes/_layout/admin_.cohorts")

function mountInvite() {
  render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        {React.createElement(
          InviteRoute.options.component as React.ComponentType,
        )}
      </QueryClientProvider>
    </React.StrictMode>,
  )
}

afterEach(() => {
  cleanup()
  queryClient.clear()
  localStorage.clear()
  sessionStorage.clear()
  navigate.mockClear()
  calls = 0
  mode = "success"
})

test("StrictMode 只兌換一次，切換帳號清除舊資料，重開邀請保留受試者", async () => {
  token = "first"
  queryClient.setQueryData(["currentUser"], { id: "previous-account" })
  localStorage.setItem("access_token", "previous-account-token")
  sessionStorage.setItem("pretestResult", "previous-account-result")
  mountInvite()
  await waitFor(() => expect(navigate).toHaveBeenCalledTimes(1))
  expect(calls).toBe(1)
  expect(localStorage.getItem("access_token")).toBe("access-first")
  expect(sessionStorage.getItem("pretestResult")).toBeNull()
  expect(queryClient.getQueryData(["currentUser"])).toBeUndefined()
  // 試測不做入門前測：直接進房間，吉祥物帶去綜合檢測
  expect(navigate.mock.calls[0][0]).toEqual({ to: "/", replace: true })
  cleanup()
  mountInvite()
  await waitFor(() => expect(navigate).toHaveBeenCalledTimes(2))
  expect(calls).toBe(1)
})

test("無效邀請顯示白話錯誤，重試會重新兌換", async () => {
  token = "invalid"
  mode = "failure"
  mountInvite()
  await screen.findByRole("alert")
  expect(screen.getByRole("alert").textContent).toContain("過期或不存在")
  expect(calls).toBe(1)
  mode = "success"
  fireEvent.click(screen.getByRole("button", { name: "再試一次" }))
  await waitFor(() => expect(navigate).toHaveBeenCalledTimes(1))
  expect(calls).toBe(2)
})

test("兌換達上限時顯示等待一分鐘", async () => {
  token = "limited"
  mode = "limited"
  mountInvite()
  await screen.findByRole("alert")
  expect(screen.getByRole("alert").textContent).toContain("等一分鐘")
  expect(navigate).not.toHaveBeenCalled()
})

test("建立梯次、顯示成員、產生邀請網址、下載圖片與 CSV、停用邀請", async () => {
  render(
    <QueryClientProvider client={queryClient}>
      {React.createElement(AdminRoute.options.component as React.ComponentType)}
    </QueryClientProvider>,
  )
  await screen.findByText("還沒有試測梯次。")
  fireEvent.change(screen.getByLabelText("新梯次名稱"), {
    target: { value: "  第一梯  " },
  })
  fireEvent.change(screen.getByLabelText("新梯次最後一天（留空是不限期限）"), {
    target: { value: "2026-11-30" },
  })
  fireEvent.submit(screen.getByLabelText("新梯次名稱").closest("form")!)
  await screen.findAllByText("T-0001")
  expect(createBody).toEqual({
    name: "第一梯",
    expires_at: "2026-11-30T23:59:59+08:00",
  })
  // 卡片寫人數、名額、期限；進度表寫每個人缺什麼
  expect(
    screen.getByText("已加入 1 人・名額 60 人・2026/11/2 到期"),
  ).toBeTruthy()
  expect(screen.getByText("檢測沒有交卷、問卷沒填")).toBeTruthy()
  // 名額與期限清空就是不限
  expect(
    (
      screen.getByLabelText("名額（留空是不限）", {
        selector: "#cohort-quota",
      }) as HTMLInputElement
    ).value,
  ).toBe("60")
  expect(
    (screen.getByLabelText("最後一天（留空是不限期限）") as HTMLInputElement)
      .value,
  ).toBe("2026-11-02")
  fireEvent.change(
    screen.getByLabelText("名額（留空是不限）", { selector: "#cohort-quota" }),
    {
      target: { value: "" },
    },
  )
  fireEvent.change(screen.getByLabelText("最後一天（留空是不限期限）"), {
    target: { value: "" },
  })
  // 改名
  fireEvent.change(screen.getByLabelText("梯次名稱"), {
    target: { value: " 第一梯（延長） " },
  })
  fireEvent.click(screen.getByRole("button", { name: "儲存設定" }))
  await screen.findByText("已儲存。")
  expect(toggleBody).toEqual({
    name: "第一梯（延長）",
    max_members: null,
    expires_at: null,
  })
  // 點受試編號看詳情
  fireEvent.click(screen.getAllByRole("button", { name: "T-0001" })[0])
  await screen.findByText("情境對抗聊過 2 場（有回過訊息的，含還沒判斷的）。")
  // 前測每題收在摺疊裡
  expect(screen.getByText("客服來電說要解除分期")).toBeTruthy()
  fireEvent.keyDown(document.activeElement ?? document.body, {
    key: "Escape",
  })
  expect(qrValue).toBe(`${window.location.origin}/invite/invitation-token`)
  fireEvent.click(screen.getByRole("button", { name: "下載邀請圖片" }))
  expect(downloads[0]).toEqual({
    href: "data:image/png;base64,TEST",
    filename: "invite-cohort-one.png",
  })
  fireEvent.click(screen.getByRole("button", { name: "下載作答資料" }))
  await waitFor(() => expect(downloads).toHaveLength(2))
  expect(downloads[1].filename).toBe("cohort-cohort-one.csv")
  expect(downloads[1].href).toStartWith("blob:")
  fireEvent.click(screen.getByRole("button", { name: "下載檢測作答 CSV" }))
  await waitFor(() => expect(downloads).toHaveLength(3))
  expect(downloads[2].filename).toBe("cohort-cohort-one-exam.csv")
  expect(downloads[2].href).toStartWith("blob:")
  fireEvent.click(screen.getByRole("button", { name: "下載問卷 CSV" }))
  await waitFor(() => expect(downloads).toHaveLength(4))
  expect(downloads[3].filename).toBe("cohort-cohort-one-survey.csv")
  fireEvent.click(screen.getByRole("button", { name: "停用邀請" }))
  await screen.findByText("邀請已停用，既有成員仍可繼續練習。")
  expect(toggleBody).toEqual({ is_active: false })
})

test("數據分析分頁：預設看全部梯次合計", async () => {
  render(
    <QueryClientProvider client={queryClient}>
      {React.createElement(AdminRoute.options.component as React.ComponentType)}
    </QueryClientProvider>,
  )
  fireEvent.click(await screen.findByRole("tab", { name: "數據分析" }))
  await screen.findByText("試測數據（1 人）")
  expect(analyticsScope).toBeUndefined()
  expect(screen.getByText("問卷分析")).toBeTruthy()
  expect(screen.getByText("還沒有問卷可以分析。")).toBeTruthy()
})
