import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_shell/")({
  component: () => <div>首頁（稍後實作）</div>,
})
