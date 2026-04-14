import { motion } from "framer-motion"

interface NarrativeCardProps {
  narrative: string
  question: string
}

export function NarrativeCard({ narrative, question }: NarrativeCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="rounded-xl border bg-card p-6 shadow-sm"
    >
      <p className="leading-relaxed text-muted-foreground">{narrative}</p>
      <p className="mt-4 text-lg font-semibold leading-relaxed">{question}</p>
    </motion.div>
  )
}
