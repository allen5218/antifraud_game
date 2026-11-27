import { createFileRoute, redirect } from "@tanstack/react-router"

/** 舊的養成與配裝頁：配裝、鍛造、圖紙收掉，玩法說明與榮譽都搬到分頁「經營」 */
export const Route = createFileRoute("/_shell/progression")({
  beforeLoad: () => {
    throw redirect({ to: "/room" })
  },
})
