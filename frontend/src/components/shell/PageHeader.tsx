import { Link } from "@tanstack/react-router"

const TITLES: { prefix: string; title: string }[] = [
  { prefix: "/scenarios", title: "情境對抗" },
  { prefix: "/quick/swipe", title: "滑卡訓練" },
  { prefix: "/quick/quiz", title: "訊息判讀" },
  { prefix: "/daily", title: "每日訓練" },
  { prefix: "/leaderboard", title: "排行榜" },
  { prefix: "/exam", title: "檢測" },
  { prefix: "/assets", title: "我的資產" },
  { prefix: "/shop", title: "商店" },
  { prefix: "/me", title: "我的" },
  { prefix: "/team", title: "團隊題庫" },
]

export function pageTitle(pathname: string): string {
  const found = TITLES.find(
    (item) =>
      pathname === item.prefix || pathname.startsWith(`${item.prefix}/`),
  )
  return found?.title ?? ""
}

export function PageHeader({ title }: { title: string }) {
  return (
    <header className="sticky top-0 z-20 grid grid-cols-[4.5rem_1fr_4.5rem] items-center border-b bg-background px-3 py-3">
      <Link to="/" className="text-sm font-bold text-foreground">
        回房間
      </Link>
      <h1 className="truncate text-center text-sm font-bold">{title}</h1>
      <span aria-hidden="true" />
    </header>
  )
}
