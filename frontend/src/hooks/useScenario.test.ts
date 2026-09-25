import { describe, expect, it } from "bun:test"
import { newScenarioError } from "./useScenario"

const apiError = (detail: unknown) => ({ body: { detail } })

describe("newScenarioError", () => {
  it("names the type and the daily limit", () => {
    expect(
      newScenarioError(
        apiError({ code: "daily_limit_reached", limit: 5 }),
        "romance",
      ),
    ).toBe("今天「假交友」已經練了 5 場，明天再來。")
  })

  it("points to the unfinished conversation", () => {
    expect(newScenarioError(apiError({ code: "active_exists" }), "atm")).toBe(
      "「解除分期」還有一場沒聊完，先回聯絡人把它聊完。",
    )
  })

  it("falls back to a generic message", () => {
    expect(newScenarioError(new Error("boom"), "atm")).toBe(
      "開不了新對話，請稍後再試。",
    )
  })
})
