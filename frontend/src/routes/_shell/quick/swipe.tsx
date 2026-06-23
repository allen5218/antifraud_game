import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_shell/quick/swipe")({
  component: SwipePage,
})

function SwipePage() {
  return <div>滑卡（載入中…）</div>
}
