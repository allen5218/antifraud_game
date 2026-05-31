import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_shell/assets")({
  component: () => <div>資產（稍後實作）</div>,
})
