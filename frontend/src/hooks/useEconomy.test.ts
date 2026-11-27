import { describe, expect, it } from "bun:test"
import { extractErrorCode } from "./useEconomy"

describe("extractErrorCode", () => {
  it("reads the code from a structured error", () => {
    expect(
      extractErrorCode({ body: { detail: { code: "insufficient_cash" } } }),
    ).toBe("insufficient_cash")
  })

  it("falls back to a plain string detail", () => {
    expect(extractErrorCode({ body: { detail: "Not Found" } })).toBe(
      "Not Found",
    )
    expect(extractErrorCode(new Error("x"))).toBeUndefined()
  })
})
