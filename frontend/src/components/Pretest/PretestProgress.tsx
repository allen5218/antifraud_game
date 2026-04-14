import { motion } from "framer-motion"

interface PretestProgressProps {
  current: number
  total: number
}

export function PretestProgress({ current, total }: PretestProgressProps) {
  const percentage = (current / total) * 100

  return (
    <div className="w-full">
      <div className="mb-2 flex justify-between text-sm text-muted-foreground">
        <span>
          第 {current} / {total} 題
        </span>
        <span>{Math.round(percentage)}%</span>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
        <motion.div
          className="h-full rounded-full bg-primary"
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        />
      </div>
    </div>
  )
}
