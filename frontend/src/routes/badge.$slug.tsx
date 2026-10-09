import { createFileRoute } from "@tanstack/react-router"
import { PublicBadge } from "@/components/exam/PublicBadge"
export const Route = createFileRoute("/badge/$slug")({
  component: BadgePage,
  head: () => ({
    meta: [
      { title: "徽章查驗 - ScamGym 識詐練習場" },
      { name: "robots", content: "noindex" },
    ],
  }),
})
function BadgePage() {
  const { slug } = Route.useParams()
  return <PublicBadge key={slug} slug={slug} />
}
