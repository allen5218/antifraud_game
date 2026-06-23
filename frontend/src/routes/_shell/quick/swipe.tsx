import { createFileRoute } from "@tanstack/react-router"
import { SwipeDeck } from "@/components/swipe/SwipeDeck"

export const Route = createFileRoute("/_shell/quick/swipe")({
  component: SwipePage,
})

function SwipePage() {
  return <SwipeDeck />
}
