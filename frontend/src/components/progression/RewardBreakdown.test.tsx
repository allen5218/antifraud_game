import { expect, test } from "bun:test"
import { fireEvent, render, screen } from "@testing-library/react"
import { RewardBreakdown } from "./RewardBreakdown"

test("收據顯示後端實際金額與信譽多給的錢，保留大整數，不再有鍛造能量", () => {
  render(
    <RewardBreakdown
      receipt={{
        receipt_id: "receipt-12345678",
        source_kind: "quiz",
        config_version: "estate-v1",
        base: { cash: "176", training_xp: 80 },
        factors: { cash: "1.14" },
        final: {
          cash_total: "9007199254740993",
          cash_bonus: "246",
        },
        core_level_before: 0,
        core_level_after: 0,
      }}
    />,
  )
  expect(screen.getByText("+9,007,199,254,740,993 元")).toBeTruthy()
  expect(screen.getByText("信譽多給 246 元")).toBeTruthy()
  expect(screen.queryByText(/鍛造|養成經驗|核心/)).toBeNull()
  fireEvent.click(screen.getByRole("button", { name: /收據/ }))
  expect(screen.getByText("estate-v1")).toBeTruthy()
})
