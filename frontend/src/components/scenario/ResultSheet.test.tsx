import { afterEach, describe, expect, it } from "bun:test"
import { cleanup, render, screen } from "@testing-library/react"
import { ResultSheet } from "./ResultSheet"

afterEach(cleanup)

const base = {
  persona_name: "投資群組帶單老師",
  flags: [{ tag: "greed", label: "貪念誘惑", detail: "保證獲利幾乎都是詐騙" }],
  xp_delta: 15,
  case_provenance: null,
}

describe("<ResultSheet />", () => {
  it("renders win reveal with reward", () => {
    render(
      <ResultSheet
        result={{
          ...base,
          outcome: "win_report",
          true_role: "scam",
          cash_delta: 1500,
          new_cash: 9000,
          triggers_forced_sell: false,
        }}
        onBack={() => {}}
        onGoAssets={() => {}}
      />,
    )
    expect(screen.getByText("識破成功!")).toBeTruthy()
    expect(screen.getByText(/\+\$1,500/)).toBeTruthy()
    expect(screen.getByText(/貪念誘惑/)).toBeTruthy()
  })

  it("renders lose reveal with forced-sell warning", () => {
    render(
      <ResultSheet
        result={{
          ...base,
          outcome: "lose_scammed",
          true_role: "scam",
          cash_delta: -12000,
          xp_delta: 0,
          new_cash: -500,
          triggers_forced_sell: true,
        }}
        onBack={() => {}}
        onGoAssets={() => {}}
      />,
    )
    expect(screen.getByText("你被騙了…")).toBeTruthy()
    expect(screen.getByText(/-\$12,000/)).toBeTruthy()
    expect(screen.getByText(/強制變賣/)).toBeTruthy()
  })

  it("shows case provenance when present", () => {
    render(
      <ResultSheet
        result={{
          ...base,
          outcome: "win_report",
          true_role: "scam",
          cash_delta: 1500,
          new_cash: 9000,
          triggers_forced_sell: false,
          case_provenance: "改編自:165 反詐騙宣導案例",
        }}
        onBack={() => {}}
        onGoAssets={() => {}}
      />,
    )
    expect(
      screen.getByText(/本情境素材 改編自:165 反詐騙宣導案例/),
    ).toBeTruthy()
  })
})
