import { motion } from "framer-motion"

interface GradeDisplayProps {
  grade: string
  totalScore: number
  correctRate: number
}

const gradeColors: Record<string, string> = {
  S: "text-yellow-500",
  A: "text-green-500",
  B: "text-blue-500",
  C: "text-muted-foreground",
}

export function GradeDisplay({
  grade,
  totalScore,
  correctRate,
}: GradeDisplayProps) {
  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", damping: 12, stiffness: 150, delay: 0.2 }}
      className="flex flex-col items-center py-6"
    >
      <div
        className={`text-8xl font-black ${gradeColors[grade] ?? "text-foreground"}`}
      >
        {grade}
      </div>
      <div className="mt-4 flex gap-6 text-center">
        <div>
          <p className="text-2xl font-bold">{totalScore}</p>
          <p className="text-sm text-muted-foreground">總分</p>
        </div>
        <div className="h-12 w-px bg-border" />
        <div>
          <p className="text-2xl font-bold">{Math.round(correctRate * 100)}%</p>
          <p className="text-sm text-muted-foreground">正確率</p>
        </div>
      </div>
    </motion.div>
  )
}
