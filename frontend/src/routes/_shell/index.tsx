import { createFileRoute } from "@tanstack/react-router"
import { RoomScene } from "@/components/room/RoomScene"

export const Route = createFileRoute("/_shell/")({
  component: Home,
})

export function Home() {
  return <RoomScene />
}
