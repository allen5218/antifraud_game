import { motion } from "framer-motion"
import Markdown from "react-markdown"

interface AnswerFeedbackProps {
  isCorrect: boolean
  explanation: string
  scoreEarned: number
  onContinue: () => void
}

export function AnswerFeedback({
  isCorrect,
  explanation,
  scoreEarned,
  onContinue,
}: AnswerFeedbackProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`rounded-xl border-2 p-5 ${
        isCorrect
          ? "border-green-500/30 bg-green-500/10"
          : "border-red-500/30 bg-red-500/10"
      }`}
    >
      <div className="mb-3 flex items-center gap-2">
        <span className="text-2xl">{isCorrect ? "✅" : "❌"}</span>
        <span
          className={`text-lg font-bold ${
            isCorrect
              ? "text-green-700 dark:text-green-400"
              : "text-red-700 dark:text-red-400"
          }`}
        >
          {isCorrect ? "答對了！" : "答錯了"}
        </span>
        {scoreEarned > 0 && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring" }}
            className="ml-auto rounded-full bg-primary px-3 py-1 text-sm font-bold text-primary-foreground"
          >
            +{scoreEarned} 分
          </motion.span>
        )}
      </div>
      <div className="mb-4 leading-relaxed text-muted-foreground prose prose-sm dark:prose-invert max-w-none">
        <Markdown>{explanation}</Markdown>
      </div>
      <button
        type="button"
        onClick={onContinue}
        className="w-full rounded-lg bg-primary py-3 font-semibold text-primary-foreground transition-transform hover:scale-[1.01] active:scale-[0.99]"
      >
        繼續
      </button>
    </motion.div>
  )
}
