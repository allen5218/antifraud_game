// 卡片插圖的排位：讀題庫的 art 欄位、決定每個角色與道具畫在 400×300 畫面的哪裡。純函式，不碰 DOM。

import {
  type CastId,
  isCastId,
  isPose,
  isPropId,
  isSceneId,
  type Pose,
  PROP_MOUNT,
  type PropId,
  type SceneId,
} from "./cardArtManifest"

export const ART_W = 400
export const ART_H = 300
/** 角色腳底踩的高度 */
export const GROUND_Y = 286
export const MAX_ITEMS = 3

export interface Rect {
  x: number
  y: number
  w: number
  h: number
}

/** phone-screen 場景裡螢幕的範圍（和 scripts/cast/scenes.ts 的 PHONE_SCREEN 一致） */
export const PHONE_SCREEN: Rect = { x: 128, y: 74, w: 144, h: 210 }
/** 視訊通話右上角的小視窗 */
export const PHONE_PIP: Rect = { x: 214, y: 84, w: 50, h: 66 }

// 角色畫布 200×240：頭中心在 y=80，腳底在 y=226
const CAST_ASPECT = 200 / 240
const CAST_FOOT = 226 / 240
const CAST_HEAD = 80 / 240
// 放地上的道具，影子（接地點）在 120×120 畫布裡的高度
const PROP_FOOT: Partial<Record<PropId, number>> = {
  atm: 114 / 120,
  parcel: 104 / 120,
  house: 106 / 120,
}

export interface CardArtInput {
  scene?: string | null
  cast?: readonly string[] | null
  props?: readonly string[] | null
  pose?: string | null
}

export interface CardArtSpec {
  scene: SceneId | null
  cast: { id: CastId; pose: Pose }[]
  props: PropId[]
}

export interface CastSlot {
  id: CastId
  pose: Pose
  x: number
  y: number
  w: number
  h: number
  /** 左右翻過來（站在右邊的人面向主角） */
  mirror: boolean
  /** 只畫在這個範圍裡（手機螢幕、視訊小視窗） */
  clip: Rect | null
}

export interface PropSlot {
  id: PropId
  x: number
  y: number
  size: number
  /** 浮著的小東西底下墊白色圓底 */
  bubble: boolean
}

export interface CardArtLayout {
  cast: CastSlot[]
  props: PropSlot[]
}

/**
 * 讀 art 欄位：清單外的 id 丟掉、最多各三個。
 * pose 只套在第一個角色（主角）；`"grandma:worried"` 可以個別指定表情。
 */
export function parseCardArt(input: CardArtInput): CardArtSpec {
  const scene = input.scene && isSceneId(input.scene) ? input.scene : null
  const cast: CardArtSpec["cast"] = []
  for (const entry of input.cast ?? []) {
    const [id, own] = entry.split(":")
    if (!isCastId(id)) continue
    const lead = cast.length === 0 ? input.pose : null
    const pose =
      own && isPose(own) ? own : lead && isPose(lead) ? lead : "neutral"
    cast.push({ id, pose })
    if (cast.length === MAX_ITEMS) break
  }
  const props: PropId[] = []
  for (const id of input.props ?? []) {
    if (!isPropId(id) || props.includes(id)) continue
    props.push(id)
    if (props.length === MAX_ITEMS) break
  }
  return { scene, cast, props }
}

// 角色高度：人越多越小；有道具時再小一點
const CAST_H = [0, 232, 214, 190]
const CAST_H_WITH_PROPS = [0, 222, 200, 170]

function standing(
  people: CardArtSpec["cast"],
  left: number,
  right: number,
  heights: number[],
): CastSlot[] {
  const k = people.length
  const h = heights[k]
  const w = h * CAST_ASPECT
  return people.map((p, i) => {
    const cx = left + ((right - left) * (2 * i + 1)) / (2 * k)
    return {
      ...p,
      x: cx - w / 2,
      y: GROUND_Y - h * CAST_FOOT,
      w,
      h,
      mirror: k > 1 && i === k - 1,
      clip: null,
    }
  })
}

/** 大道具並排放在地上，小道具在上面的空間由上往下排 */
function placeProps(
  ids: PropId[],
  left: number,
  right: number,
  maxSize: number,
  column: boolean,
): PropSlot[] {
  const ground = ids.filter((id) => PROP_MOUNT[id] === "ground")
  const float = ids.filter((id) => PROP_MOUNT[id] === "float")
  const width = right - left
  const top = 24
  const slots: PropSlot[] = []
  // 橫排（畫面上沒有人）：每個道具一格，地上的貼地、浮的放在中間高度
  if (!column) {
    const cell = width / ids.length
    const size = Math.min(maxSize, cell - 10)
    ids.forEach((id, i) => {
      const x = left + cell * (i + 0.5) - size / 2
      const foot = PROP_FOOT[id]
      slots.push(
        foot
          ? { id, x, y: GROUND_Y - size * foot, size, bubble: false }
          : { id, x, y: (top + GROUND_Y) / 2 - size / 2, size, bubble: true },
      )
    })
    return slots
  }
  let floorTop = GROUND_Y
  if (ground.length) {
    const cell = width / ground.length
    const size = Math.min(maxSize, cell)
    ground.forEach((id, i) => {
      const y = GROUND_Y - size * (PROP_FOOT[id] ?? 1)
      floorTop = Math.min(floorTop, y)
      slots.push({
        id,
        x: left + cell * (i + 0.5) - size / 2,
        y,
        size,
        bubble: false,
      })
    })
  }
  if (float.length) {
    const cell = (floorTop - top - 6) / float.length
    const size = Math.min(maxSize, cell - 6)
    float.forEach((id, i) => {
      slots.push({
        id,
        x: (left + right) / 2 - size / 2,
        y: top + cell * i + (cell - size) / 2,
        size,
        bubble: true,
      })
    })
  }
  return slots
}

/** 手機螢幕場景：主角在螢幕裡像視訊，第二人在右上角小視窗，第三人站在手機左邊 */
function phoneLayout(spec: CardArtSpec): CardArtLayout {
  const cast: CastSlot[] = []
  const [lead, second, third] = spec.cast
  // 讓頭的中心落在 (中心點 x, 中心點 y)，頭以下被 clip 裁掉
  const bust = (
    p: CardArtSpec["cast"][number],
    h: number,
    cx: number,
    headY: number,
    clip: Rect,
    mirror: boolean,
  ): CastSlot => {
    const w = h * CAST_ASPECT
    return { ...p, x: cx - w / 2, y: headY - h * CAST_HEAD, w, h, mirror, clip }
  }
  if (lead)
    cast.push(
      bust(
        lead,
        270,
        PHONE_SCREEN.x + PHONE_SCREEN.w / 2,
        PHONE_SCREEN.y + 80,
        PHONE_SCREEN,
        false,
      ),
    )
  // 小視窗要放得下整顆頭（含頭髮），再露一點肩膀
  if (second)
    cast.push(
      bust(
        second,
        118,
        PHONE_PIP.x + PHONE_PIP.w / 2,
        PHONE_PIP.y + PHONE_PIP.h / 2,
        PHONE_PIP,
        true,
      ),
    )
  if (third) cast.push(...standing([third], 8, 112, [0, 190]))
  return { cast, props: placeProps(spec.props, 286, 396, 104, true) }
}

export function layoutCardArt(spec: CardArtSpec): CardArtLayout {
  if (spec.scene === "phone-screen") return phoneLayout(spec)
  const hasCast = spec.cast.length > 0
  const hasProps = spec.props.length > 0
  const cast = hasCast
    ? hasProps
      ? standing(spec.cast, 8, 272, CAST_H_WITH_PROPS)
      : standing(spec.cast, 16, 384, CAST_H)
    : []
  const props = hasProps
    ? hasCast
      ? placeProps(spec.props, 282, 392, 110, true)
      : placeProps(spec.props, 40, 360, 150, false)
    : []
  return { cast, props }
}
