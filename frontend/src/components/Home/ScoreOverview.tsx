import { motion } from "framer-motion"
import { useEffect, useState } from "react"
import { ScoreService } from "@/client"

interface ScoreData {
  total_score: number
  games_played: number
  level: number
}

export function ScoreOverview() {
  const [data, setData] = useState<ScoreData | null>(null)

  useEffect(() => {
    ScoreService.getMyScore()
      .then((res: any) => setData(res))
      .catch(() => {})
  }, [])

  if (!data) return null

  const stats = [
    { label: "總積分", value: data.total_score },
    { label: "等級", value: `Lv.${data.level}` },
    { label: "已完成遊戲", value: `${data.games_played} 次` },
  ]

  return (
    <div className="grid grid-cols-3 gap-4">
      {stats.map((stat, i) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
          className="rounded-xl border bg-card p-4 text-center shadow-sm"
        >
          <p className="text-2xl font-bold">{stat.value}</p>
          <p className="mt-1 text-sm text-muted-foreground">{stat.label}</p>
        </motion.div>
      ))}
    </div>
  )
}
