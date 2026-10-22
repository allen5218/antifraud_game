/** 團隊題庫列表：對照題排法、篩選、答案顯示與留言。 */
import { afterEach, expect, mock, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react"
import type { TeamBank, TeamCase } from "@/client"

const actualClient = await import("@/client")
const created: unknown[] = []
mock.module("@/client", () => ({
  ...actualClient,
  TeamService: {
    ...actualClient.TeamService,
    listComments: async () => [
      {
        id: "c1",
        item_kind: "case",
        item_key: "shop-scam-1",
        body: "價差太大",
        author: "小明",
        mine: true,
        created_at: "2026-10-22T01:00:00Z",
      },
    ],
    createComment: async ({ requestBody }: { requestBody: unknown }) => {
      created.push(requestBody)
      return {}
    },
  },
}))

const { TeamBankList, pairCases } = await import("./TeamBank")

afterEach(cleanup)

function makeCase(overrides: Partial<TeamCase>): TeamCase {
  return {
    key: "k",
    pool: "practice",
    fraud_type: "shopping",
    is_scam: true,
    difficulty: 1,
    title: "標題",
    narrative: "敘述",
    red_flags: [{ tag: "greed", text: "便宜很多" }],
    provenance: "改編自：測試",
    mirror_key: null,
    pattern_key: null,
    ...overrides,
  }
}

const bank: TeamBank = {
  pretest: [
    {
      key: "pre-1",
      fraud_type: "atm",
      is_scam: true,
      difficulty: 1,
      question: "銀行打來要你去提款機",
      options: [
        { key: "A", text: "照做", is_correct: false },
        { key: "B", text: "掛斷自己打給銀行", is_correct: true },
      ],
      explanation: "銀行不會要你去提款機解除設定",
    },
  ],
  swipe: [],
  cases: [
    makeCase({
      key: "shop-legit-1",
      is_scam: false,
      mirror_key: "shop-scam-1",
      red_flags: [{ tag: null, text: "走平台購物車" }],
    }),
    makeCase({ key: "shop-scam-1", title: "社團裡的主機" }),
    makeCase({ key: "atm-scam-1", fraud_type: "atm", title: "解除分期" }),
    makeCase({
      key: "exam-1",
      pool: "exam_tactics",
      red_flags: [
        { tag: "greed", text: "超便宜" },
        { tag: "time_pressure", text: "今天就要" },
      ],
    }),
  ],
  questions: [],
  personas: [],
  skills: [],
  tactic_labels: { greed: "用好處引誘你", time_pressure: "催你快點決定" },
  comment_counts: { "case:shop-scam-1": 1 },
}

function renderList(
  tab: "pretest" | "quiz" | "exam",
  filters = { type: "all", truth: "all" as const, query: "" },
) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <TeamBankList bank={bank} tab={tab} filters={filters} />
    </QueryClientProvider>,
  )
}

test("詐騙題後面緊接它的對照正常題", () => {
  expect(pairCases(bank.cases).map((c) => c.key)).toEqual([
    "atm-scam-1",
    "exam-1",
    "shop-scam-1",
    "shop-legit-1",
  ])
})

test("前測標出正解", () => {
  renderList("pretest")
  const correct = screen.getByLabelText("正解").closest("li")
  expect(correct?.textContent).toContain("掛斷自己打給銀行")
})

test("訊息判讀只列練習題，類型與搜尋會篩選", () => {
  renderList("quiz")
  expect(screen.getByText("共 3 筆")).toBeTruthy()
  expect(screen.queryByText("exam-1")).toBeNull()
  cleanup()
  renderList("quiz", { type: "shopping", truth: "all", query: "" })
  expect(screen.getByText("共 2 筆")).toBeTruthy()
  cleanup()
  renderList("quiz", { type: "all", truth: "legit", query: "" })
  expect(screen.getByText("共 1 筆")).toBeTruthy()
  cleanup()
  renderList("quiz", { type: "all", truth: "all", query: "解除分期" })
  expect(screen.getByText("共 1 筆")).toBeTruthy()
})

test("檢測的話術題列出要勾的話術", () => {
  renderList("exam")
  expect(screen.getByText("共 1 筆")).toBeTruthy()
  expect(screen.getByText("用好處引誘你、催你快點決定")).toBeTruthy()
})

test("打開討論看得到留言，送出新留言", async () => {
  renderList("quiz", { type: "shopping", truth: "scam", query: "" })
  fireEvent.click(screen.getByRole("button", { name: /討論（1）/ }))
  await waitFor(() => expect(screen.getByText("價差太大")).toBeTruthy())
  const box = screen.getByLabelText("留言")
  fireEvent.change(box, { target: { value: "  改成三成  " } })
  fireEvent.click(
    within(box.closest("form") as HTMLElement).getByRole("button", {
      name: "留言",
    }),
  )
  await waitFor(() =>
    expect(created).toEqual([
      { item_kind: "case", item_key: "shop-scam-1", body: "改成三成" },
    ]),
  )
})
