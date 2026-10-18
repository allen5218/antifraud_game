import { describe, expect, test } from "bun:test"
import {
  badgeRects,
  clampStage,
  ROOM_STAGE_COUNT,
  ROOM_WORLD,
  roomBackground,
  roomBoxes,
  roomLayers,
} from "./roomArt"
import { ROOM_BOXES } from "./roomArtLayout"
import { coreRect, type Rect } from "./stage"

describe("roomArt", () => {
  test("房間階段夾在 0 到 6", () => {
    expect(clampStage(-1)).toBe(0)
    expect(clampStage(2.7)).toBe(2)
    expect(clampStage(99)).toBe(6)
    expect(clampStage(Number.NaN)).toBe(0)
  })

  test("七間都畫好了", () => {
    expect(ROOM_BOXES).toHaveLength(ROOM_STAGE_COUNT)
    expect(ROOM_BOXES.every((boxes) => boxes !== null)).toBe(true)
    expect(roomBackground(4)).toBe("/assets/room/4/bg.webp")
  })

  // 核心是 3:4 平板到 9:21 長手機都看得到的範圍
  const core = coreRect(ROOM_WORLD)
  const overlap = (r: Rect) =>
    (Math.max(0, Math.min(r.x + r.w, core.x + core.w) - Math.max(r.x, core.x)) *
      Math.max(
        0,
        Math.min(r.y + r.h, core.y + core.h) - Math.max(r.y, core.y),
      )) /
    (r.w * r.h)

  for (let stage = 0; stage < ROOM_STAGE_COUNT; stage++) {
    // 使用者 10-18：「手機在窄比例容易消失」——手機要完整在核心裡，還要留邊
    test(`第 ${stage} 間：手機在最細長的手機上也完整看得到`, () => {
      const phone = roomBoxes(stage).phone
      const margin = ROOM_WORLD.width * 0.02
      expect(phone.x).toBeGreaterThanOrEqual(core.x + margin)
      expect(phone.x + phone.w).toBeLessThanOrEqual(core.x + core.w - margin)
      expect(phone.y).toBeGreaterThanOrEqual(core.y + margin)
      expect(phone.y + phone.h).toBeLessThanOrEqual(core.y + core.h - margin)
    })

    // 原本貼著畫面邊緣的書櫃、電視往外補完後會有一小塊在核心外，最長的手機上會被裁到一點
    test(`第 ${stage} 間：其他可以點的東西中心在核心裡、大部分看得到`, () => {
      for (const layer of roomLayers(stage, "/m.webp")) {
        const r = layer.box
        const cx = r.x + r.w / 2
        const cy = r.y + r.h / 2
        expect(cx).toBeGreaterThan(core.x)
        expect(cx).toBeLessThan(core.x + core.w)
        expect(cy).toBeGreaterThan(core.y)
        expect(cy).toBeLessThan(core.y + core.h)
        expect(overlap(r)).toBeGreaterThanOrEqual(0.7)
      }
    })
  }

  test("剪下來的家具圖在各自的資料夾，吉祥物用傳進來的圖", () => {
    const srcs = Object.fromEntries(
      roomLayers(5, "/m.webp").map((layer) => [layer.id, layer.src]),
    )
    expect(srcs.tv).toBe("/assets/room/5/tv.webp")
    expect(srcs.mascot).toBe("/m.webp")
  })

  test("徽章最多六個，擺在書櫃的兩層上", () => {
    const boxes = roomBoxes(3)
    const rects = badgeRects(boxes, 9)
    expect(rects).toHaveLength(6)
    const shelf = boxes.bookshelf
    for (const r of rects) {
      expect(r.x).toBeGreaterThanOrEqual(shelf.x)
      expect(r.x + r.w).toBeLessThanOrEqual(shelf.x + shelf.w)
      expect(r.y).toBeGreaterThanOrEqual(shelf.y)
      expect(r.y + r.h).toBeLessThanOrEqual(shelf.y + shelf.h)
    }
  })
})
