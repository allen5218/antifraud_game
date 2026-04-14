import { motion } from "framer-motion"

interface OptionButtonProps {
  optionKey: string
  text: string
  state: "default" | "selected" | "correct" | "wrong" | "dimmed"
  disabled: boolean
  onClick: () => void
}

const stateStyles: Record<string, string> = {
  default: "border-border bg-card hover:border-primary/50 hover:bg-accent",
  selected: "border-primary bg-primary/10",
  correct:
    "border-green-500 bg-green-500/10 text-green-700 dark:text-green-400",
  wrong: "border-red-500 bg-red-500/10 text-red-700 dark:text-red-400",
  dimmed: "border-border bg-card opacity-50",
}

export function OptionButton({
  optionKey,
  text,
  state,
  disabled,
  onClick,
}: OptionButtonProps) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      disabled={disabled}
      whileTap={!disabled ? { scale: 0.98 } : undefined}
      className={`w-full rounded-xl border-2 px-5 py-4 text-left text-base font-medium transition-colors ${stateStyles[state]}`}
    >
      <span className="mr-3 inline-flex h-7 w-7 items-center justify-center rounded-full border-2 border-current text-sm font-bold">
        {optionKey}
      </span>
      {text}
    </motion.button>
  )
}
