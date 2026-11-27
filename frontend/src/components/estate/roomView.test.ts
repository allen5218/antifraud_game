import { expect, test } from "bun:test"
import { showsRoomScene } from "./roomView"

test("平常顯示經營，年長者、導覽、我的家顯示房間", () => {
  expect(showsRoomScene({ elder: false })).toBe(false)
  expect(showsRoomScene({ elder: true })).toBe(true)
  expect(showsRoomScene({ elder: false, tour: 1 })).toBe(true)
  expect(showsRoomScene({ elder: false, view: "house" })).toBe(true)
  expect(showsRoomScene({ elder: false, tourPending: true })).toBe(true)
  expect(showsRoomScene({ elder: false, view: "other" })).toBe(false)
})
