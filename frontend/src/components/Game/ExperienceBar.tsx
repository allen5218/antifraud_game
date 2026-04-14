import { motion } from "framer-motion"

interface ExperienceBarProps {
  score: number
  level: number
  currentStep: number
  maxSteps: number
}

export function ExperienceBar({
  score,
  level,
  currentStep,
  maxSteps,
}: ExperienceBarProps) {
  const progress = (currentStep / maxSteps) * 100

  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground">
          Lv.{level}
        </div>
        <motion.span
          key={score}
          initial={{ scale: 1.3, color: "hsl(var(--primary))" }}
          animate={{ scale: 1, color: "hsl(var(--foreground))" }}
          transition={{ duration: 0.4 }}
          className="text-lg font-bold"
        >
          {score} 分
        </motion.span>
      </div>

      <div className="flex-1">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>
            第 {currentStep} / {maxSteps} 題
          </span>
        </div>
        <div className="mt-1 h-2.5 w-full overflow-hidden rounded-full bg-muted">
          <motion.div
            className="h-full rounded-full bg-primary"
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.4, ease: "easeOut" }}
          />
        </div>
      </div>
    </div>
  )
}
