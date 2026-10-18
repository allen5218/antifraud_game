import { afterEach, expect, it, mock } from "bun:test"
import { act, cleanup, render, waitFor } from "@testing-library/react"
import { toast } from "sonner"

import * as actualThemes from "next-themes"

// mock.module 會留給之後的測試檔，只覆寫 useTheme、其他照原模組
mock.module("next-themes", () => ({
  ...actualThemes,
  useTheme: () => ({ theme: "light" }),
}))

import { Toaster } from "./sonner"

afterEach(cleanup)

// 2026-10-18 正式環境：手機上「有新版本」提示蓋住房間左下的購物、房子按鈕
it("手機上的提示離底部留出按鈕的高度", async () => {
  render(<Toaster />)
  await act(async () => {
    toast("有新版本")
  })
  // sonner 用 portal 把提示放在 body 底下，不在 render 的 container 裡
  const list = await waitFor(() => {
    const el = document.querySelector<HTMLElement>("[data-sonner-toaster]")
    if (!el) throw new Error("提示還沒出現")
    return el
  })
  expect(list.style.getPropertyValue("--mobile-offset-bottom")).toBe(
    "calc(env(safe-area-inset-bottom) + 4.5rem)",
  )
})
