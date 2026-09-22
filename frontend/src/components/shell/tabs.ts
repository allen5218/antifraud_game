import {
  Building2,
  House,
  type LucideIcon,
  MessagesSquare,
  UserRound,
} from "lucide-react"

/** 手機底部分頁與桌機側欄共用同一份定義,不要各自維護一份。 */
export interface TabDef {
  to: string
  icon: LucideIcon
  label: string
  testId: string
}

export const TABS: TabDef[] = [
  { to: "/", icon: House, label: "首頁", testId: "tab-home" },
  {
    to: "/scenarios",
    icon: MessagesSquare,
    label: "情境",
    testId: "tab-scenarios",
  },
  { to: "/assets", icon: Building2, label: "資產", testId: "tab-assets" },
  { to: "/me", icon: UserRound, label: "我", testId: "tab-me" },
]

export function isTabActive(pathname: string, to: string): boolean {
  return to === "/"
    ? pathname === "/"
    : pathname === to || pathname.startsWith(`${to}/`)
}
