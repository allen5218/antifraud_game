import { createFileRoute } from "@tanstack/react-router"
import { CardPlayer } from "@/components/cards/CardPlayer"
import { FRAUD_TYPES } from "@/lib/fraudTypes"

const TOPICS = new Set<string>([...FRAUD_TYPES, "general"])

/** 日常卡片練習。`?topic=atm` 只練某一類，沒帶就照間隔重複與練習重點混著出。 */
export const Route = createFileRoute("/_shell/learn")({
  component: LearnPage,
  validateSearch: (search: Record<string, unknown>): { topic?: string } => {
    const topic = typeof search.topic === "string" ? search.topic : undefined
    return topic && TOPICS.has(topic) ? { topic } : {}
  },
})

function LearnPage() {
  const { topic } = Route.useSearch()
  return <CardPlayer key={topic ?? "all"} topic={topic ?? null} />
}
