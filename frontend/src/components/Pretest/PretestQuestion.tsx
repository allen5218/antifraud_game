import { AnimatePresence, motion } from "framer-motion"
import { useState } from "react"

interface Option {
  key: string
  text: string
}

interface PretestQuestionProps {
  questionText: string
  options: Option[]
  onAnswer: (selectedKey: string) => void
}

export function PretestQuestion({
  questionText,
  options,
  onAnswer,
}: PretestQuestionProps) {
  const [selected, setSelected] = useState<string | null>(null)

  const handleSelect = (key: string) => {
    if (selected) return
    setSelected(key)
    setTimeout(() => {
      onAnswer(key)
      setSelected(null)
    }, 300)
  }

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={questionText}
        initial={{ opacity: 0, x: 40 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -40 }}
        transition={{ duration: 0.3 }}
        className="flex flex-col gap-6"
      >
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <p className="text-lg font-medium leading-relaxed">{questionText}</p>
        </div>

        <div className="flex flex-col gap-3">
          {options.map((option) => (
            <button
              key={option.key}
              type="button"
              onClick={() => handleSelect(option.key)}
              disabled={selected !== null}
              className={`w-full rounded-xl border-2 px-5 py-4 text-left text-base font-medium transition-all
                ${
                  selected === option.key
                    ? "border-primary bg-primary/10 scale-[0.98]"
                    : "border-border bg-card hover:border-primary/50 hover:bg-accent"
                }
                ${selected !== null && selected !== option.key ? "opacity-50" : ""}
              `}
            >
              <span className="mr-3 inline-flex h-7 w-7 items-center justify-center rounded-full border-2 border-current text-sm font-bold">
                {option.key}
              </span>
              {option.text}
            </button>
          ))}
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
