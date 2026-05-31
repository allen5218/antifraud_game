import { createFileRoute, Link } from "@tanstack/react-router"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_shell/me")({
  component: Me,
})

function Me() {
  const { user } = useAuth()
  return (
    <div className="flex flex-col gap-3 py-4 text-center">
      <span className="text-5xl">🐱</span>
      <h2 className="text-lg font-bold">
        {user?.full_name || user?.email || "載入中…"}
      </h2>
      <Link to="/settings" className="text-xs text-primary underline">
        舊版設定（過渡）
      </Link>
      <p className="text-[10px] text-muted-foreground">
        個人頁完整內容後續 spec
      </p>
    </div>
  )
}
