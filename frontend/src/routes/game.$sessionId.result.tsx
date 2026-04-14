import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router"
import { motion } from "framer-motion"
import type { GameOverResult } from "@/client"
import { GradeDisplay } from "@/components/GameResult/GradeDisplay"
import { WeaknessAnalysis } from "@/components/GameResult/WeaknessAnalysis"
import { WeaknessRadar } from "@/components/GameResult/WeaknessRadar"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/game/$sessionId/result")({
  component: GameResultPage,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({ to: "/login" })
    }
  },
  head: () => ({
    meta: [{ title: "遊戲結果 - 反詐騙訓練" }],
  }),
})

function GameResultPage() {
  const navigate = useNavigate()

  const stored = sessionStorage.getItem("gameResult")
  if (!stored) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground">找不到遊戲結果</p>
          <button
            type="button"
            onClick={() => navigate({ to: "/" })}
            className="mt-4 rounded-lg bg-primary px-6 py-2 text-primary-foreground"
          >
            回首頁
          </button>
        </div>
      </div>
    )
  }

  const result: GameOverResult = JSON.parse(stored)

  const handlePlayAgain = () => {
    sessionStorage.removeItem("gameResult")
    navigate({ to: "/pretest" })
  }

  const handleGoHome = () => {
    sessionStorage.removeItem("gameResult")
    navigate({ to: "/" })
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-2xl flex-col px-4 py-8">
      <motion.h1
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center text-2xl font-bold"
      >
        遊戲結果
      </motion.h1>

      <GradeDisplay
        grade={result.grade}
        totalScore={result.total_score}
        correctRate={result.correct_rate}
      />

      {result.weakness_analysis.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-4"
        >
          <WeaknessRadar weaknesses={result.weakness_analysis} />
        </motion.div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="mt-6"
      >
        <WeaknessAnalysis
          weaknesses={result.weakness_analysis}
          strengths={result.strength_tags}
        />
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="mt-8 flex gap-4"
      >
        <button
          type="button"
          onClick={handlePlayAgain}
          className="flex-1 rounded-xl bg-primary py-3 font-semibold text-primary-foreground transition-transform hover:scale-[1.01] active:scale-[0.99]"
        >
          再玩一次
        </button>
        <button
          type="button"
          onClick={handleGoHome}
          className="flex-1 rounded-xl border-2 border-border py-3 font-semibold transition-transform hover:scale-[1.01] active:scale-[0.99]"
        >
          回首頁
        </button>
      </motion.div>
    </div>
  )
}
