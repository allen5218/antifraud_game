import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_shell/me")({
  component: () => <div>我（稍後實作）</div>,
})
