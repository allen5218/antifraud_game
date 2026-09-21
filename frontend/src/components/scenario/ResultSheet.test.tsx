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
      screen.getByText(/本情境素材.*改編自:165 反詐騙宣導案例/),
    ).toBeTruthy()
  })

  it("describes a contact story as an event instead of accusing the contact", () => {
    render(
      <ResultSheet
        result={{
          ...base,
          persona_name: "生前告別狂歡派對企劃",
          outcome: "safe_exit",
          true_role: "scam_event",
          cash_delta: 0,
          new_cash: 1000,
          triggers_forced_sell: false,
          reward_breakdown: {
            base_cash: 0,
            chapter_level: 0,
            chapter_multiplier: 1,
            chat_bonuses: { full_service_objective: 0.2 },
            total_chat_factor: 0.2,
            is_chapter_finale: false,
            final_cash: 0,
            final_xp: 12,
            is_replay: false,
          },
        }}
        onBack={() => {}}
        onGoAssets={() => {}}
      />,
    )
    expect(
      screen.getByText(
        (_, element) =>
          element?.tagName === "P" &&
          element.textContent?.includes("事件真相：詐騙事件") === true,
      ),
    ).toBeTruthy()
    expect(screen.queryByText(/薇姐.*詐騙者/)).toBeNull()
    expect(screen.getAllByText("+20%")).toHaveLength(2)
    expect(screen.getByText("服務目標達成加成")).toBeTruthy()
  })

  it("renders permanent formula matching exact formula format: $800 × 1.32（天梯）× 1.30（本案）= $1,373", () => {
    render(
      <ResultSheet
        result={{
          ...base,
          outcome: "win_report",
          true_role: "scam",
          cash_delta: 1373,
          new_cash: 11373,
          triggers_forced_sell: false,
          reward_breakdown: {
            base_cash: 800,
            chapter_level: 2,
            chapter_multiplier: 1.32,
            chapter_subtotal: 1056,
            chat_bonuses: { effective_tool_info: 0.1, full_service_objective: 0.2 },
            total_chat_factor: 0.3,
            is_chapter_finale: false,
            final_cash: 1373,
            final_xp: 15,
            is_replay: false,
          },
        }}
        onBack={() => {}}
        onGoAssets={() => {}}
      />,
    )
    const formulaEl = screen.getByTestId("settlement-formula")
    expect(formulaEl.textContent).toBe(
      "$800 × 1.32（天梯）× 1.30（本案）= $1,373",
    )
    expect(screen.getByText(/小計 \$1,056/)).toBeTruthy()
  })

  it("renders replay mode with clean 0 reward and replay badge", () => {
    render(
      <ResultSheet
        result={{
          ...base,
          outcome: "win_report",
          true_role: "scam",
          cash_delta: 0,
          new_cash: 10000,
          triggers_forced_sell: false,
          reward_breakdown: {
            base_cash: 800,
            chapter_level: 2,
            chapter_multiplier: 1.32,
            chat_bonuses: {},
            total_chat_factor: 0,
            is_chapter_finale: false,
            final_cash: 0,
            final_xp: 0,
            is_replay: true,
          },
        }}
        onBack={() => {}}
        onGoAssets={() => {}}
      />,
    )
    expect(screen.getByText("純練習重玩")).toBeTruthy()
    const formulaEl = screen.getByTestId("settlement-formula")
    expect(formulaEl.textContent).toContain("重玩練習")
  })

  it("renders chapter finale multiplier in formula: × 2.50（終局）", () => {
    render(
      <ResultSheet
        result={{
          ...base,
          outcome: "win_report",
          true_role: "scam",
          cash_delta: 2640,
          new_cash: 12640,
          triggers_forced_sell: false,
          reward_breakdown: {
            base_cash: 800,
            chapter_level: 2,
            chapter_multiplier: 1.32,
            chat_bonuses: {},
            total_chat_factor: 0,
            is_chapter_finale: true,
            final_cash: 2640,
            final_xp: 25,
            is_replay: false,
          },
        }}
        onBack={() => {}}
        onGoAssets={() => {}}
      />,
    )
    const formulaEl = screen.getByTestId("settlement-formula")
    expect(formulaEl.textContent).toBe(
      "$800 × 1.32（天梯）× 2.50（終局）= $2,640",
    )
  })
})
