import { createFileRoute } from "@tanstack/react-router"
import { AccrualBanner } from "@/components/Home/AccrualBanner"
import { LadderJourney } from "@/components/Home/LadderJourney"

export const Route = createFileRoute("/_shell/")({
  component: Home,
})

export function Home() {
  return (
    <div className="space-y-3 pb-4">
      <LadderJourney />
      <AccrualBanner />
    </div>
  )
}
