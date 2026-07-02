import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_shell/scenarios/$scenarioId")({
  component: ScenarioChatPage,
})

function ScenarioChatPage() {
  const { scenarioId } = Route.useParams()
  return <div data-testid="chat-skeleton">{scenarioId}</div>
}
