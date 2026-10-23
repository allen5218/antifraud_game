/** 聊天畫面：日期分隔、時間、已讀、對方頭貼與名字、被擋訊息的提示。 */
import { afterEach, expect, test } from "bun:test"
import { cleanup, render, screen } from "@testing-library/react"
import { chatDay, chatTime, MessageList, toChatEntries } from "./MessageList"
import { messageRejection } from "./messageRejection"

afterEach(cleanup)

test("chatDay 寫今天、昨天，更早寫日期與星期", () => {
  const now = new Date(2026, 9, 23, 15, 0)
  expect(chatDay(new Date(2026, 9, 23, 1, 0).toISOString(), now)).toBe("今天")
  expect(chatDay(new Date(2026, 9, 22, 23, 0).toISOString(), now)).toBe("昨天")
  expect(chatDay(new Date(2026, 9, 20, 9, 0).toISOString(), now)).toBe(
    "10月20日（二）",
  )
  expect(chatTime(null)).toBe("")
  expect(chatTime("not a date")).toBe("")
})

test("對方訊息有頭貼和名字，玩家訊息對方回過才標已讀", () => {
  const at = new Date().toISOString()
  const entries = toChatEntries([
    { role: "npc", messages: ["嗨", "在嗎"], decision_point: null, at },
    { role: "player", text: "你好", at },
    { role: "npc", messages: ["最近好嗎"], decision_point: null, at },
    { role: "player", text: "還不錯" },
  ])
  render(
    <MessageList
      entries={entries}
      typing={true}
      avatar="romance-1"
      name="Sunny"
    />,
  )
  expect(screen.getAllByText("Sunny")).toHaveLength(2)
  // 日期分隔只出現一次
  expect(screen.getAllByText("今天")).toHaveLength(1)
  // 第一則玩家訊息之後對方回過；最後一則還沒
  expect(screen.getAllByText("已讀")).toHaveLength(1)
  // 舊紀錄沒有時間不顯示；有時間的三段各顯示一次
  expect(document.querySelectorAll("time")).toHaveLength(3)
  expect(screen.getByTestId("typing-indicator").textContent).toContain(
    "輸入中…",
  )
})

test("被擋下的訊息有對應提示，其他錯誤回 null", () => {
  expect(messageRejection("message_blocked")).toContain("不適合")
  expect(messageRejection("message_too_long")).toContain("200")
  expect(messageRejection("message_garbled")).toContain("看不懂")
  expect(messageRejection("agent_failed")).toBeNull()
})
