import type { HotspotId } from "./logic"
import { ROOM_BOXES } from "./roomArtLayout"
import type { Rect, Size } from "./stage"

/**
 * 房間的圖層：每一間（stage-0～6，跟著擁有的最高房產）是一整張畫好家具的房間圖（bg.webp），
 * 再從同一張圖剪下可點的家具（書櫃、月曆、信件架、電視、手機），疊回原來的位置。
 * 剪下來的圖和底圖是同一張畫、同一個位置，所以一定對齊；圖層只用來做呼吸光與點擊範圍。
 * 方框由 antifraud_video 的 cut_room_layers.py 產生（roomArtLayout.ts），世界圖 941×1672。
 */

export type RoomTarget = HotspotId | "mascot"
export type CutId = "bookshelf" | "calendar" | "letters" | "tv" | "phone"
export type Box = Rect

export type RoomBoxes = Record<CutId | "mascot", Box> & {
  /** 書櫃中間兩層擺徽章的位置（y＝層板表面） */
  shelves: { x0: number; x1: number; y: number }[]
}

export type RoomLayer = {
  id: CutId | "mascot"
  src: string
  box: Box
  target: RoomTarget
}

export const ROOM_WORLD: Size = { width: 941, height: 1672 }
export const ROOM_STAGE_COUNT = 7
// 還沒畫好的房間先用這一間
const FALLBACK_STAGE = 3

// 由後往前畫：吉祥物坐在扶手椅上，電視與桌上的手機在它前面
const ORDER: RoomLayer["id"][] = [
  "bookshelf",
  "calendar",
  "letters",
  "mascot",
  "tv",
  "phone",
]

export function clampStage(stage: number): number {
  const rounded = Number.isFinite(stage) ? Math.trunc(stage) : 0
  return Math.min(ROOM_STAGE_COUNT - 1, Math.max(0, rounded))
}

/** 這一間實際用哪一組圖（還沒畫好的用備用那間） */
function artStage(stage: number): number {
  const s = clampStage(stage)
  return ROOM_BOXES[s] ? s : FALLBACK_STAGE
}

export function roomBoxes(stage: number): RoomBoxes {
  const boxes = ROOM_BOXES[artStage(stage)]
  if (!boxes) throw new Error("房間圖層資料缺少備用的那一間")
  return boxes
}

export function roomBackground(stage: number): string {
  return `/assets/room/${artStage(stage)}/bg.webp`
}

export function roomLayers(stage: number, mascotSrc: string): RoomLayer[] {
  const s = artStage(stage)
  const boxes = roomBoxes(s)
  return ORDER.map((id) => ({
    id,
    src: id === "mascot" ? mascotSrc : `/assets/room/${s}/${id}.webp`,
    box: boxes[id],
    target: id,
  }))
}

/** 檢測徽章擺在書櫃中間兩層，每層三個 */
export const MAX_SHELF_BADGES = 6

export function badgeRects(boxes: RoomBoxes, count: number): Rect[] {
  const rects: Rect[] = []
  for (const shelf of boxes.shelves) {
    const size = ((shelf.x1 - shelf.x0) / 3) * 0.8
    for (let i = 0; i < 3; i++) {
      const center = shelf.x0 + ((shelf.x1 - shelf.x0) / 3) * (i + 0.5)
      rects.push({ x: center - size / 2, y: shelf.y - size, w: size, h: size })
    }
  }
  return rects.slice(0, Math.min(count, MAX_SHELF_BADGES))
}
