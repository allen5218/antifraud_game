import { createFileRoute } from "@tanstack/react-router"
import { AccrualBanner } from "@/components/Home/AccrualBanner"
import { ChapterBanner } from "@/components/Home/ChapterBanner"
import { PlayModeGrid } from "@/components/Home/PlayModeGrid"

export const Route = createFileRoute("/_shell/")({
  component: Home,
})

function Home() {
  return (
    <>
      <AccrualBanner />
      <ChapterBanner />
      <PlayModeGrid />
    </>
  )
}
