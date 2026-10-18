import { describe, expect, test } from "bun:test"
import {
  clampToView,
  coreRect,
  layoutStage,
  shiftIntoView,
  toScreen,
} from "./stage"

const WORLD = { width: 941, height: 1672 }

function visible(viewW: number, viewH: number) {
  const { scale, x, y } = layoutStage(WORLD, viewW, viewH)
  return {
    left: -x / scale,
    top: -y / scale,
    right: (viewW - x) / scale,
    bottom: (viewH - y) / scale,
    scale,
    x,
    y,
  }
}

describe("layoutStage", () => {
  const core = coreRect(WORLD)
  const cases: [string, number, number][] = [
    ["9:16 手機", 360, 640],
    ["19.5:9 手機", 390, 844],
    ["9:21 長手機", 360, 840],
    ["瀏覽器網址列擠掉高度的手機", 390, 660],
    ["iPad 直放", 768, 1024],
    ["平板橫放", 1180, 820],
    ["桌機", 1440, 900],
  ]
  for (const [name, w, h] of cases) {
    test(`${name}：核心完整看得到`, () => {
      const v = visible(w, h)
      expect(v.left).toBeLessThanOrEqual(core.x + 0.01)
      expect(v.top).toBeLessThanOrEqual(core.y + 0.01)
      expect(v.right).toBeGreaterThanOrEqual(core.x + core.w - 0.01)
      expect(v.bottom).toBeGreaterThanOrEqual(core.y + core.h - 0.01)
    })
  }

  for (const [name, w, h] of cases.slice(0, 5)) {
    test(`${name}：直式範圍內鋪滿，不留邊`, () => {
      const v = visible(w, h)
      expect(v.left).toBeGreaterThanOrEqual(-0.01)
      expect(v.top).toBeGreaterThanOrEqual(-0.01)
      expect(v.right).toBeLessThanOrEqual(WORLD.width + 0.01)
      expect(v.bottom).toBeLessThanOrEqual(WORLD.height + 0.01)
    })
  }

  test("比 3:4 寬的畫面：房間置中，兩側留底色", () => {
    const { x, scale } = layoutStage(WORLD, 1440, 900)
    expect(x).toBeGreaterThan(0)
    expect(x * 2 + WORLD.width * scale).toBeCloseTo(1440)
  })

  test("還沒量到大小時不縮放", () => {
    expect(layoutStage(WORLD, 0, 0)).toEqual({ scale: 0, x: 0, y: 0 })
  })
})

test("toScreen 把世界座標換成畫面位置", () => {
  expect(
    toScreen({ x: 100, y: 200, w: 50, h: 40 }, { scale: 0.5, x: 10, y: -20 }),
  ).toEqual({ x: 60, y: 80, w: 25, h: 20 })
})

test("clampToView 把跑出畫面的方框夾回來，留邊", () => {
  expect(clampToView({ x: 350, y: 700, w: 80, h: 60 }, 390, 740)).toEqual({
    x: 350,
    y: 700,
    w: 32,
    h: 32,
  })
  expect(clampToView({ x: -20, y: 10, w: 100, h: 50 }, 390, 740)).toEqual({
    x: 8,
    y: 10,
    w: 72,
    h: 50,
  })
})

test("shiftIntoView 大小不變、整塊移進畫面", () => {
  expect(shiftIntoView({ x: 330, y: 714, w: 44, h: 50 }, 360, 840)).toEqual({
    x: 308,
    y: 714,
    w: 44,
    h: 50,
  })
})
