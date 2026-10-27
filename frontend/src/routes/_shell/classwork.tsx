import { createFileRoute } from "@tanstack/react-router"
import { Classwork } from "@/components/classroom/Classwork"

export const Route = createFileRoute("/_shell/classwork")({
  component: Classwork,
  head: () => ({ meta: [{ title: "班級作業 - ScamGym 識詐練習場" }] }),
})
