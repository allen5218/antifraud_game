import type { HotspotId } from "./logic"

/** 房間物件各自通往的玩法 */
export const HOTSPOT_LINKS = {
  phone: { to: "/scenarios", label: "情境對抗" },
  tv: { to: "/quick/swipe", label: "滑卡訓練" },
  letters: { to: "/quick/quiz", label: "訊息判讀" },
  calendar: { to: "/daily", label: "每日訓練" },
  bookshelf: { to: "/exam", label: "檢測" },
} as const satisfies Record<
  HotspotId,
  {
    to: "/scenarios" | "/quick/swipe" | "/quick/quiz" | "/daily" | "/exam"
    label: string
  }
>
