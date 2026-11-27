import {
  Building2,
  Layers,
  type LucideIcon,
  MessageCircle,
  UserRound,
} from "lucide-react"

/**
 * 一般模式的四個分頁（2026-11 改版，照 Stitch 定稿）：練習、訊息、經營、我的。
 * 手機底部分頁與桌機側欄共用同一份定義，不要各自維護一份。
 * 「訊息」目前是情境對抗，「經營」目前是房間；之後換成新版的收件匣與放置經營。
 */
export interface TabDef {
  to: "/" | "/scenarios" | "/room" | "/me"
  icon: LucideIcon
  label: string
  testId: string
}

export const TABS: TabDef[] = [
  { to: "/", icon: Layers, label: "練習", testId: "tab-learn" },
  {
    to: "/scenarios",
    icon: MessageCircle,
    label: "訊息",
    testId: "tab-messages",
  },
  { to: "/room", icon: Building2, label: "經營", testId: "tab-room" },
  { to: "/me", icon: UserRound, label: "我的", testId: "tab-me" },
]

/** 練習分頁包含卡片練習頁本身 */
export function isTabActive(pathname: string, to: string): boolean {
  if (to === "/") return pathname === "/" || pathname.startsWith("/learn")
  return pathname === to || pathname.startsWith(`${to}/`)
}
