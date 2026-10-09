import { expect, test } from "bun:test"
import { clearInviteSessions, INVITE_SESSION_PREFIX } from "./inviteSession"

test("登出時清掉所有邀請憑證，其他資料不動", () => {
  localStorage.clear()
  localStorage.setItem(`${INVITE_SESSION_PREFIX}aaa`, "{}")
  localStorage.setItem(`${INVITE_SESSION_PREFIX}bbb`, "{}")
  localStorage.setItem("theme", "dark")
  clearInviteSessions()
  expect(localStorage.getItem(`${INVITE_SESSION_PREFIX}aaa`)).toBeNull()
  expect(localStorage.getItem(`${INVITE_SESSION_PREFIX}bbb`)).toBeNull()
  expect(localStorage.getItem("theme")).toBe("dark")
})
