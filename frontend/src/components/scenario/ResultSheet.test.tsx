import { afterEach, describe, expect, it } from "bun:test"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { ResultSheet } from "./ResultSheet"

afterEach(cleanup)

const base = {
  persona_name: "投資群組帶單老師",
  flags: [
    { tag: "greed", label: "用好處引誘你", detail: "保證獲利幾乎都是詐騙" },
  ],
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
    expect(screen.getByText("識破成功！")).toBeTruthy()
    expect(screen.getByText(/\+\$1,500/)).toBeTruthy()
    expect(screen.getByText(/用好處引誘你/)).toBeTruthy()
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
    expect(screen.getByText("你被騙了")).toBeTruthy()
    expect(screen.getByText(/-\$12,000/)).toBeTruthy()
    expect(screen.getByText(/變賣房產/)).toBeTruthy()
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
          case_provenance: "改編自：165 反詐騙宣導案例",
        }}
        onBack={() => {}}
        onGoAssets={() => {}}
      />,
    )
    expect(screen.getByText("改編自：165 反詐騙宣導案例")).toBeTruthy()
  })

  const win = {
    ...base,
    outcome: "win_report",
    true_role: "scam",
    cash_delta: 1500,
    new_cash: 9000,
    triggers_forced_sell: false,
  }

  it("offers one more round of the practice focus", () => {
    let started = 0
    render(
      <ResultSheet
        result={win}
        onBack={() => {}}
        onGoAssets={() => {}}
        next={{
          fraudType: "romance",
          onStart: () => started++,
          pending: false,
          notice: "今天「假交友」已經練了 5 場，明天再來。",
        }}
      />,
    )
    fireEvent.click(screen.getByTestId("practice-next"))
    expect(started).toBe(1)
    expect(screen.getByText("再練一場「假交友」")).toBeTruthy()
    expect(screen.getByRole("alert").textContent).toContain("5 場")
  })

  it("hides the next round while assets must be sold", () => {
    render(
      <ResultSheet
        result={{ ...win, triggers_forced_sell: true }}
        onBack={() => {}}
        onGoAssets={() => {}}
        next={{
          fraudType: "romance",
          onStart: () => {},
          pending: false,
          notice: null,
        }}
      />,
    )
    expect(screen.queryByTestId("practice-next")).toBeNull()
    expect(screen.getByText("查看資產")).toBeTruthy()
  })
})
