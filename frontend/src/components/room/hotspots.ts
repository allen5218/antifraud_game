export type Spot = { x: number; y: number }

/**
 * 百分比，相對於固定比例的房間圖框（物件的中心點）。
 * 照 stage-0 量的；七張房間的家具位置相同，所以只有一份。
 */
export const HOTSPOTS = {
  tv: { x: 12, y: 71 },
  letters: { x: 55, y: 33 },
  calendar: { x: 48, y: 18 },
  bookshelf: { x: 18, y: 32 },
  phone: { x: 91, y: 87 },
  mascot: { x: 70, y: 60 },
} as const satisfies Record<string, Spot>

/** 書櫃上兩層各三格，最多六個徽章。 */
export const BADGE_SLOTS: Spot[] = [
  { x: 10, y: 16 },
  { x: 19, y: 16 },
  { x: 28, y: 16 },
  { x: 10, y: 28 },
  { x: 19, y: 28 },
  { x: 28, y: 28 },
]
