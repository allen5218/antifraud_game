import { expect, test } from "bun:test"
import { showsTabBar } from "./TabBar"
import { isTabActive, TABS } from "./tabs"

test("四個分頁：練習、訊息、經營、我的", () => {
  expect(TABS.map((t) => t.label)).toEqual(["練習", "訊息", "經營", "我的"])
  expect(TABS.map((t) => t.to)).toEqual(["/", "/scenarios", "/room", "/me"])
})

test("卡片練習頁算在練習分頁", () => {
  expect(isTabActive("/", "/")).toBe(true)
  expect(isTabActive("/learn", "/")).toBe(true)
  expect(isTabActive("/room", "/")).toBe(false)
  expect(isTabActive("/scenarios/abc", "/scenarios")).toBe(true)
})

test("只有四個分頁本身顯示底部分頁", () => {
  expect(showsTabBar("/")).toBe(true)
  expect(showsTabBar("/room")).toBe(true)
  expect(showsTabBar("/learn")).toBe(false)
  expect(showsTabBar("/exam")).toBe(false)
})
