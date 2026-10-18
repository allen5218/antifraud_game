/**
 * 房間舞台的排版：房間畫在固定大小的「世界」裡（家具用世界座標擺），整個舞台用同一個縮放，
 * 熱區跟著家具走，不會因為螢幕比例不同而重排。
 *
 * 世界圖外圈是可以被裁掉的牆和地板（出血），中央的「核心」放所有可以點的東西：
 * 最寬到 3:4（平板直放）、最長到 9:21（長手機）都能鋪滿畫面又看得到整個核心。
 * 比 3:4 更寬的畫面（平板橫放、桌機）改成把核心完整放進畫面，外面露出底色。
 */

export type Size = { width: number; height: number }
export type Rect = { x: number; y: number; w: number; h: number }
export type StageLayout = { scale: number; x: number; y: number }

/** 支援的最寬與最長比例（寬 ÷ 高） */
export const WIDEST = 3 / 4
export const TALLEST = 9 / 21

/** 世界圖中央、任何支援的比例下都看得到的範圍 */
export function coreRect(world: Size): Rect {
  const w = Math.min(world.width, world.height * TALLEST)
  const h = Math.min(world.height, world.width / WIDEST)
  return { x: (world.width - w) / 2, y: (world.height - h) / 2, w, h }
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

/** 把世界放進寬 viewW、高 viewH 的畫面：盡量鋪滿，但核心一定完整看得到。 */
export function layoutStage(
  world: Size,
  viewW: number,
  viewH: number,
): StageLayout {
  if (viewW <= 0 || viewH <= 0) return { scale: 0, x: 0, y: 0 }
  const core = coreRect(world)
  const cover = Math.max(viewW / world.width, viewH / world.height)
  const fitCore = Math.min(viewW / core.w, viewH / core.h)
  const scale = Math.min(cover, fitCore)
  const stageW = world.width * scale
  const stageH = world.height * scale
  // 以核心中心對準畫面中心，再把邊推回去，能鋪滿的方向不留縫
  let x = viewW / 2 - (core.x + core.w / 2) * scale
  let y = viewH / 2 - (core.y + core.h / 2) * scale
  x = stageW >= viewW ? clamp(x, viewW - stageW, 0) : (viewW - stageW) / 2
  y = stageH >= viewH ? clamp(y, viewH - stageH, 0) : (viewH - stageH) / 2
  return { scale, x, y }
}

/** 世界座標的方框換成畫面上的位置（給不跟著縮放的泡泡、數字用） */
export function toScreen(rect: Rect, layout: StageLayout): Rect {
  return {
    x: layout.x + rect.x * layout.scale,
    y: layout.y + rect.y * layout.scale,
    w: rect.w * layout.scale,
    h: rect.h * layout.scale,
  }
}

/**
 * 把畫面上的方框夾進可見範圍（留 inset 的邊）：物件被裁到一點時，
 * 點擊範圍和右上角的紅色標記仍留在畫面裡，不會跟著跑出去。
 */
export function clampToView(
  rect: Rect,
  viewW: number,
  viewH: number,
  inset = 8,
): Rect {
  const x0 = Math.max(rect.x, inset)
  const y0 = Math.max(rect.y, inset)
  const x1 = Math.min(rect.x + rect.w, viewW - inset)
  const y1 = Math.min(rect.y + rect.h, viewH - inset)
  return { x: x0, y: y0, w: Math.max(0, x1 - x0), h: Math.max(0, y1 - y0) }
}

/** 方框大小不變，整塊移進可見範圍（留 inset 的邊）；比畫面還大時貼齊左上 */
export function shiftIntoView(
  rect: Rect,
  viewW: number,
  viewH: number,
  inset = 8,
): Rect {
  const x = Math.max(inset, Math.min(rect.x, viewW - inset - rect.w))
  const y = Math.max(inset, Math.min(rect.y, viewH - inset - rect.h))
  return { ...rect, x, y }
}
