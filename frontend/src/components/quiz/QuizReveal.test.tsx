import { afterEach, describe, expect, it } from "bun:test"
import { cleanup, render, screen } from "@testing-library/react"
import { QuizReveal } from "./QuizReveal"

afterEach(cleanup)

const result = {
  correct: true,
  is_scam: true,
  red_flags: [
    { tag: "greed", text: "保證獲利穩賺不賠" },
    { tag: "time_pressure", text: "名額只到今晚" },
  ],
  provenance: "改編自:司法院裁判書詐欺案件",
}

describe("<QuizReveal />", () => {
  it("shows verdict, flags with tags and provenance", () => {
    render(<QuizReveal result={result} onNext={() => {}} isLast={false} />)
    expect(screen.getByText(/答對了/)).toBeTruthy()
    expect(screen.getByText(/保證獲利穩賺不賠/)).toBeTruthy()
    expect(screen.getByText("greed")).toBeTruthy()
    expect(screen.getByText(/改編自:司法院裁判書詐欺案件/)).toBeTruthy()
  })

  it("shows wrong verdict for incorrect", () => {
    render(
      <QuizReveal
        result={{ ...result, correct: false }}
        onNext={() => {}}
        isLast
      />,
    )
    expect(screen.getByText(/答錯了/)).toBeTruthy()
    expect(screen.getByText(/看結算/)).toBeTruthy()
  })
})
