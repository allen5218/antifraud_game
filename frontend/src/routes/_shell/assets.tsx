import { createFileRoute, redirect } from "@tanstack/react-router"

/** 舊的「我的資產」頁：房產改成放置經營，搬到分頁「經營」 */
export const Route = createFileRoute("/_shell/assets")({
  beforeLoad: () => {
    throw redirect({ to: "/room" })
  },
})
