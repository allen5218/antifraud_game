/**
 * LINE Integration SDK & Theme Helpers for Antifraud Game
 */

export interface LineUser {
  userId: string
  displayName: string
  pictureUrl?: string
  statusMessage?: string
}

export interface LineSticker {
  packageId: string
  stickerId: string
  url: string
}

// Default simulated LINE Stickers
export const LINE_STICKERS: Record<string, string> = {
  shocked: "https://p.line-scdn.net/sticker_pack/default/1/sticker_1.png",
  suspicious: "https://p.line-scdn.net/sticker_pack/default/1/sticker_2.png",
  ok: "https://p.line-scdn.net/sticker_pack/default/1/sticker_3.png",
  scam_alert: "https://p.line-scdn.net/sticker_pack/default/1/sticker_4.png",
}

/**
 * LIFF (LINE Front-end Framework) Bridge initialization check
 */
export function isRunningInLiff(): boolean {
  if (typeof window === "undefined") return false
  return !!(window as unknown as { liff?: unknown }).liff
}

export function getSimulatedLineUser(): LineUser {
  return {
    userId: "U1234567890lineuser",
    displayName: "反詐玩家",
    pictureUrl: "https://api.dicebear.com/7.x/bottts/svg?seed=antifraud",
    statusMessage: "防詐防護中",
  }
}
