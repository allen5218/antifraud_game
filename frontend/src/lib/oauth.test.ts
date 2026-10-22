import { beforeEach, expect, test } from "bun:test"
import { challengeFor, makeVerifier, savePending, takePending } from "./oauth"

beforeEach(() => sessionStorage.clear())

test("code_challenge 是 verifier 的 SHA-256、base64url 不留等號", async () => {
  // 期望值用 Python 的 hashlib 與 base64.urlsafe_b64encode 另外算
  expect(
    await challengeFor("dBjftJeZ4CVP-mJ92K9DmVrY4UBA2ZEi1-KH1RGy-bw"),
  ).toBe("IYA985F7afoDnnpuFD32BqYYYv1JKxrwBq542WJalzQ")
})

test("verifier 是 64 字的 base64url，每次都不同", () => {
  const a = makeVerifier()
  expect(a).toMatch(/^[A-Za-z0-9_-]{64}$/)
  expect(makeVerifier()).not.toBe(a)
})

test("待完成的登入只能取一次", () => {
  savePending({ provider: "line", state: "s", verifier: "v" })
  expect(takePending()).toEqual({ provider: "line", state: "s", verifier: "v" })
  expect(takePending()).toBeNull()
})
