import { createFileRoute } from "@tanstack/react-router"
import { AccrualBanner } from "@/components/Home/AccrualBanner"
import { PlayModeGrid } from "@/components/Home/PlayModeGrid"
import { TodayChallengeHero } from "@/components/Home/TodayChallengeHero"

export const Route = createFileRoute("/_shell/")({
  component: Home,
})

function Home() {
  return (
    <>
      <AccrualBanner />
      <TodayChallengeHero />
      <PlayModeGrid />
    </>
  )
}
