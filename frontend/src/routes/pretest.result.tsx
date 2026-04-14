import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router"
import { motion } from "framer-motion"
import { useState } from "react"
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts"

import { GameService } from "@/client"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/pretest/result")({
  component: PretestResultPage,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({ to: "/login" })
    }
  },
  head: () => ({
    meta: [{ title: "前測結果 - 反詐騙訓練" }],
  }),
})

const FRAUD_TYPE_LABELS: Record<string, string> = {
  investment: "投資詐欺",
  shopping: "假網路購物",
  "fake-sale": "偽稱買賣",
  romance: "假愛情交友",
  atm: "解除分期付款",
}

interface FraudTypeResult {
  correct: number
  total: number
}

interface PretestResult {
  results_by_type: Record<string, FraudTypeResult>
  weakest_type: string
  ready_for_game: boolean
}

function PretestResultPage() {
  const navigate = useNavigate()
  const [starting, setStarting] = useState(false)

  // 從 sessionStorage 讀取前測結果
  const stored = sessionStorage.getItem("pretestResult")
  if (!stored) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground">找不到前測結果</p>
          <button
            type="button"
            onClick={() => navigate({ to: "/pretest" })}
            className="mt-4 rounded-lg bg-primary px-6 py-2 text-primary-foreground"
          >
            重新開始前測
          </button>
        </div>
      </div>
    )
  }

  const result: PretestResult = JSON.parse(stored)

  const radarData = Object.entries(result.results_by_type).map(
    ([type, res]) => ({
      type: FRAUD_TYPE_LABELS[type] ?? type,
      score: res.total > 0 ? Math.round((res.correct / res.total) * 100) : 0,
      fullMark: 100,
    }),
  )

  const totalCorrect = Object.values(result.results_by_type).reduce(
    (sum, r) => sum + r.correct,
    0,
  )
  const totalQuestions = Object.values(result.results_by_type).reduce(
    (sum, r) => sum + r.total,
    0,
  )

  const handleStartGame = async () => {
    setStarting(true)
    try {
      const data: any = await GameService.startGame({
        requestBody: { fraud_type: result.weakest_type },
      })
      sessionStorage.removeItem("pretestResult")
      navigate({ to: `/game/${data.session_id}` as string })
    } catch {
      setStarting(false)
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-2xl flex-col items-center px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full text-center"
      >
        <h1 className="text-2xl font-bold">前測結果</h1>
        <p className="mt-2 text-muted-foreground">
          你答對了 {totalCorrect} / {totalQuestions} 題
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="my-8 w-full rounded-xl border bg-card p-4 shadow-sm"
      >
        <ResponsiveContainer width="100%" height={320}>
          <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
            <PolarGrid stroke="hsl(var(--border))" />
            <PolarAngleAxis
              dataKey="type"
              tick={{ fontSize: 12, fill: "hsl(var(--foreground))" }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
            />
            <Radar
              name="正確率"
              dataKey="score"
              stroke="hsl(var(--primary))"
              fill="hsl(var(--primary))"
              fillOpacity={0.3}
            />
          </RadarChart>
        </ResponsiveContainer>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.4 }}
        className="mb-8 w-full rounded-xl border border-orange-500/30 bg-orange-500/10 p-5 text-center"
      >
        <p className="text-sm text-muted-foreground">你最需要加強的類型是</p>
        <p className="mt-1 text-xl font-bold text-orange-600 dark:text-orange-400">
          {FRAUD_TYPE_LABELS[result.weakest_type] ?? result.weakest_type}
        </p>
        <p className="mt-2 text-sm text-muted-foreground">
          接下來的遊戲將針對這個類型進行強化訓練
        </p>
      </motion.div>

      <button
        type="button"
        onClick={handleStartGame}
        disabled={starting}
        className="w-full max-w-xs rounded-xl bg-primary px-8 py-4 text-lg font-bold text-primary-foreground transition-transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-60"
      >
        {starting ? "建立遊戲中..." : "開始遊戲訓練"}
      </button>
    </div>
  )
}
