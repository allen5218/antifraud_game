/** 試測問卷：必填檢查、選「其他」要寫說明、送出的答案格式。 */
import { afterEach, expect, test } from "bun:test"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import type { SurveyQuestionPublic } from "@/client"
import { firstMissing, sections, toggle } from "./survey"
import { TrialSurveyForm } from "./TrialSurveyForm"

afterEach(cleanup)

const AGREE = ["非常不同意", "不同意", "普通", "同意", "非常同意"]

function question(
  id: string,
  kind: SurveyQuestionPublic["kind"],
  extra: Partial<SurveyQuestionPublic> = {},
): SurveyQuestionPublic {
  return {
    id,
    kind,
    text: `題目 ${id}`,
    section: "基本資料",
    options: [],
    labels: [],
    required: true,
    other: false,
    ...extra,
  }
}

const QUESTIONS = [
  question("consent", "consent", { text: "我同意參與" }),
  question("age", "single", { options: ["18–24 歲", "25–34 歲"] }),
  question("satisfied", "scale", { labels: AGREE, section: "整體" }),
  question("occasions", "multi", {
    options: ["學校", "其他"],
    other: true,
    section: "整體",
  }),
  question("improve", "text", { required: false, section: "意見" }),
]

test("firstMissing 照題目順序找第一個沒答的必填題", () => {
  expect(firstMissing(QUESTIONS, {})).toBe("consent")
  const answers = {
    consent: true,
    age: "18–24 歲",
    satisfied: 4,
    occasions: ["其他"],
  }
  expect(firstMissing(QUESTIONS, answers)).toBe("occasions")
  expect(firstMissing(QUESTIONS, { ...answers, occasions_other: "  " })).toBe(
    "occasions",
  )
  expect(
    firstMissing(QUESTIONS, { ...answers, occasions_other: "公司" }),
  ).toBeNull()
})

test("toggle 與 sections", () => {
  expect(toggle(undefined, "學校")).toEqual(["學校"])
  expect(toggle(["學校", "其他"], "學校")).toEqual(["其他"])
  expect(sections(QUESTIONS).map((g) => g.title)).toEqual([
    "基本資料",
    "整體",
    "意見",
  ])
})

test("沒答完不能送，答完送出整理好的答案", () => {
  const sent: Record<string, unknown>[] = []
  render(
    <TrialSurveyForm
      questions={QUESTIONS}
      submitting={false}
      error={null}
      onSubmit={(answers) => sent.push(answers)}
    />,
  )
  // 量表每一點都有字
  for (const label of AGREE) expect(screen.getByText(label)).toBeTruthy()
  fireEvent.click(screen.getByRole("button", { name: "送出問卷" }))
  expect(sent).toHaveLength(0)
  expect(screen.getByRole("alert").textContent).toBe("這一題還沒完成")

  fireEvent.click(screen.getByLabelText("我同意參與"))
  fireEvent.click(screen.getByLabelText("25–34 歲"))
  fireEvent.click(screen.getByLabelText(/^4/))
  fireEvent.click(screen.getByLabelText("其他"))
  fireEvent.change(screen.getByLabelText("其他：請寫一下"), {
    target: { value: "公司訓練" },
  })
  fireEvent.click(screen.getByRole("button", { name: "送出問卷" }))
  expect(sent).toEqual([
    {
      consent: true,
      age: "25–34 歲",
      satisfied: 4,
      occasions: ["其他"],
      occasions_other: "公司訓練",
    },
  ])
})

test("後端退回時標出那一題", () => {
  render(
    <TrialSurveyForm
      questions={QUESTIONS}
      submitting={false}
      error={{ questionId: "age", message: "這一題還沒選" }}
      onSubmit={() => {}}
    />,
  )
  expect(screen.getByRole("alert").textContent).toBe("這一題還沒選")
  expect(document.getElementById("q-age")?.getAttribute("aria-invalid")).toBe(
    "true",
  )
})
