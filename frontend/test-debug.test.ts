import { describe, expect, it } from "bun:test"

describe("setup", () => {
  it("should have global document", () => {
    console.log("typeof document:", typeof document)
    expect(typeof document).toBe("object")
  })
})
