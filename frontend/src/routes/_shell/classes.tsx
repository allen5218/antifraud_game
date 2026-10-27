import { createFileRoute } from "@tanstack/react-router"
import { ClassList } from "@/components/classroom/ClassList"

export const Route = createFileRoute("/_shell/classes")({
  component: ClassList,
  head: () => ({ meta: [{ title: "班級管理 - ScamGym 識詐練習場" }] }),
})
