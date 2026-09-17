import { afterEach, describe, expect, it } from "bun:test"
import { cleanup, render, screen } from "@testing-library/react"
import { QuizReveal } from "./QuizReveal"

afterEach(cleanup)

const result = {
  type: "verdict" as const,
  correct: true,
  is_scam: true,
  red_flags: [
    { tag: "greed", text: "保證獲利穩賺不賠" },
    { tag: "time_pressure", text: "名額只到今晚" },
  ],
  provenance: "改編自:司法院裁判書詐欺案件",
  tag_details: [
    {
      tag: "greed",
      label: "貪念誘惑",
      suggestion: "保證獲利時，先停下來查證風險",
    },
    {
      tag: "time_pressure",
      label: "時間壓力",
      suggestion: "遇到限時話術先冷靜",
    },
  ],
}

const verdictItem = {
  item_id: "verdict-1",
  type: "verdict" as const,
  fraud_type: "investment",
  title: "穩賺投資",
  narrative: "加入群組立即獲利",
  difficulty: 2,
}

describe("<QuizReveal />", () => {
  it("shows verdict and localized flags without raw tags", () => {
    render(
      <QuizReveal
        item={verdictItem}
        result={result}
        onNext={() => {}}
        isLast={false}
      />,
    )
    expect(screen.getByText(/答對了/)).toBeTruthy()
    expect(screen.getByText(/保證獲利穩賺不賠/)).toBeTruthy()
    expect(screen.getAllByText("貪念誘惑")).toHaveLength(2)
    expect(screen.getByText(/先停下來查證風險/)).toBeTruthy()
    expect(screen.getByText(/改編自:司法院裁判書詐欺案件/)).toBeTruthy()
    expect(screen.queryByText("greed")).toBeNull()
  })

  it("shows wrong verdict for incorrect", () => {
    render(
      <QuizReveal
        result={{ ...result, correct: false }}
        item={verdictItem}
        onNext={() => {}}
        isLast
      />,
    )
    expect(screen.getByText(/答錯了/)).toBeTruthy()
    expect(screen.getByText(/看結算/)).toBeTruthy()
  })

  it("shows tactics missed and extra choices with teaching suggestions", () => {
    render(
      <QuizReveal
        item={{
          item_id: "tactics-1",
          type: "tactics",
          fraud_type: "investment",
          title: "限時投資",
          narrative: "今晚截止",
          difficulty: 2,
          question: "用了哪些話術？",
          options: [
            { tag: "time_pressure", label: "時間壓力" },
            { tag: "authority", label: "權威服從" },
          ],
        }}
        result={{
          type: "tactics",
          correct: false,
          correct_tags: ["time_pressure"],
          missed_tags: ["time_pressure"],
          extra_tags: ["authority"],
          tag_details: [
            {
              tag: "time_pressure",
              label: "時間壓力",
              suggestion: "先給自己冷靜期",
            },
            {
              tag: "authority",
              label: "權威服從",
              suggestion: "主動查證身份",
            },
          ],
        }}
        onNext={() => {}}
        isLast={false}
      />,
    )

    expect(screen.getByText(/漏選/)).toBeTruthy()
    expect(screen.getByText(/多選/)).toBeTruthy()
    expect(screen.getByText(/先給自己冷靜期/)).toBeTruthy()
    expect(screen.getByText(/主動查證身份/)).toBeTruthy()
  })

  it("shows each match result and suggestions for incorrect pairs", () => {
    render(
      <QuizReveal
        item={{
          item_id: "match-1",
          type: "match",
          question: "配對",
          match_prompts: [
            { pair_id: "pair-1", text: "今晚前匯款" },
            { pair_id: "pair-2", text: "我是警察" },
          ],
          match_targets: [
            { tag: "time_pressure", label: "時間壓力" },
            { tag: "authority", label: "權威服從" },
          ],
        }}
        result={{
          type: "match",
          correct: false,
          results: [
            {
              pair_id: "pair-1",
              correct_tag: "time_pressure",
              correct: false,
            },
            { pair_id: "pair-2", correct_tag: "authority", correct: true },
          ],
          tag_details: [
            {
              tag: "time_pressure",
              label: "時間壓力",
              suggestion: "先給自己冷靜期",
            },
          ],
        }}
        onNext={() => {}}
        isLast
      />,
    )

    expect(screen.getByText(/今晚前匯款/)).toBeTruthy()
    expect(screen.getByText(/正解：.*時間壓力/)).toBeTruthy()
    expect(screen.getByText(/先給自己冷靜期/)).toBeTruthy()
  })
})
