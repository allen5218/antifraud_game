import { expect, test } from "bun:test"
import { fireEvent, render, screen } from "@testing-library/react"
import { RewardBreakdown } from "./RewardBreakdown"

test("收據顯示後端實際金額與鍛造能量，保留大整數", () => {
  render(
    <RewardBreakdown
      receipt={{
        receipt_id: "receipt-12345678",
        source_kind: "quiz",
        config_version: "growth-v1.1",
        base: { cash: "176", training_xp: 80 },
        factors: { cash: "2.4", growth_xp: "2", energy: "1.8" },
        final: {
          cash_total: "9007199254740993",
          cash_bonus: "246",
          growth_xp: "160",
          forge_energy: "144",
        },
        core_level_before: 0,
        core_level_after: 1,
      }}
    />,
  )
  expect(screen.getByText("+$9,007,199,254,740,993")).toBeTruthy()
  expect(screen.getByText("+144")).toBeTruthy()
  expect(screen.getByText("+160")).toBeTruthy()
  fireEvent.click(screen.getByRole("button", { name: /收據/ }))
  expect(screen.getByText("growth-v1.1")).toBeTruthy()
})
