import { afterEach, beforeEach, expect, mock, test } from "bun:test"
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react"
import { renderWithRouter } from "@/test/renderWithRouter"

type Opts = {
  onSuccess?: (r: never) => void
  onSettled?: () => void
}

const ROUND = {
  round_id: "r1",
  daily_goal: 20,
  today_done: 0,
  cards: [
    {
      card_key: "atm-judge-001",
      kind: "judge",
      fraud_type: "atm",
      prompt: "客服：「請您到 ATM，我幫您解除分期。」",
      difficulty: 1,
      art: { scene: "atm-corner", cast: ["grandma"], props: ["atm"] },
      choices: [
        { id: "yes", text: "是詐騙" },
        { id: "no", text: "不是詐騙" },
      ],
    },
    {
      card_key: "atm-fill-001",
      kind: "fill",
      fraud_type: "atm",
      prompt: "ATM 沒有＿＿的功能。",
      difficulty: 1,
      art: { scene: "atm-corner" },
      choices: [
        { id: "f1", text: "查詢餘額" },
        { id: "f2", text: "解除分期" },
      ],
    },
  ],
}

let answered: { cardKey: string; ids: string[] }[] = []
let completed: string[] = []

mock.module("@/hooks/useCards", () => ({
  useCardRound: () => ({
    data: ROUND,
    isError: false,
    error: null,
  }),
  useAnswerCard: () => ({
    isPending: false,
    isError: false,
    error: null,
    mutate: (vars: { cardKey: string; ids: string[] }, opts: Opts) => {
      answered.push(vars)
      const right = vars.cardKey === "atm-judge-001" ? "yes" : "f2"
      opts.onSuccess?.({
        correct: vars.ids[0] === right,
        correct_ids: [right],
        explanation: "ATM 沒有解除分期的功能。",
        weakness: { tag: "authority", label: "冒充官方或專家" },
      } as never)
      opts.onSettled?.()
    },
  }),
  useCompleteRound: () => ({
    isPending: false,
    isError: false,
    mutate: (roundId: string, opts: Opts) => {
      completed.push(roundId)
      opts.onSuccess?.({
        correct_count: 1,
        total: 2,
        cash_earned: 30,
        xp_earned: 12,
        today_done: 2,
        daily_goal: 20,
      } as never)
    },
  }),
}))

const { CardPlayer, formatBoost } = await import("./CardPlayer")

beforeEach(() => {
  answered = []
  completed = []
})
afterEach(cleanup)

test("一張一張作答，答完看解說，最後看結果", async () => {
  await renderWithRouter(<CardPlayer topic={null} />)
  expect(await screen.findByText(ROUND.cards[0].prompt)).toBeTruthy()

  // 連點只送一次
  const yes = screen.getByRole("button", { name: "是詐騙" })
  fireEvent.click(yes)
  fireEvent.click(yes)
  expect(answered).toHaveLength(1)
  expect(await screen.findByText("答對了")).toBeTruthy()
  expect(screen.getByText("對方用的招數：冒充官方或專家")).toBeTruthy()

  fireEvent.click(screen.getByRole("button", { name: "下一張" }))
  fireEvent.click(await screen.findByRole("button", { name: "查詢餘額" }))
  expect(await screen.findByText("答錯了，過幾天會再考一次")).toBeTruthy()
  // 填空題答完把正解填進空格
  expect(screen.getAllByText("解除分期").length).toBeGreaterThan(0)

  fireEvent.click(screen.getByRole("button", { name: "看結果" }))
  await waitFor(() => expect(completed).toEqual(["r1"]))
  expect(await screen.findByTestId("round-summary")).toBeTruthy()
  expect(screen.getByText("1／2")).toBeTruthy()
  expect(screen.getByText("今天 2／20 張")).toBeTruthy()
})

test("練習加速的時間寫成幾小時幾分鐘", () => {
  expect(formatBoost(20)).toBe("20 分鐘")
  expect(formatBoost(120)).toBe("2 小時")
  expect(formatBoost(160)).toBe("2 小時 40 分鐘")
})
