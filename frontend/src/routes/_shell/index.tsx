import { createFileRoute } from "@tanstack/react-router"
import { ExamActiveNotice } from "@/components/exam/ExamActiveNotice"
import { AccrualBanner } from "@/components/Home/AccrualBanner"
import { NextStepHero } from "@/components/Home/NextStepHero"
import { PlayModeGrid } from "@/components/Home/PlayModeGrid"

export const Route = createFileRoute("/_shell/")({
  component: Home,
})

export function Home() {
  return (
    <>
      <ExamActiveNotice />
      <AccrualBanner />
      <NextStepHero />
      <PlayModeGrid />
    </>
  )
}
