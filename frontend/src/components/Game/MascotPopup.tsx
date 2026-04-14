import { AnimatePresence, motion } from "framer-motion"
import { useEffect } from "react"

interface MascotPopupProps {
  show: boolean
  message: string
  onDismiss: () => void
}

export function MascotPopup({ show, message, onDismiss }: MascotPopupProps) {
  useEffect(() => {
    if (!show) return
    const timer = setTimeout(onDismiss, 2500)
    return () => clearTimeout(timer)
  }, [show, onDismiss])

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          onClick={onDismiss}
          onKeyDown={(e) => {
            if (e.key === "Escape") onDismiss()
          }}
        >
          <motion.div
            initial={{ scale: 0.5, y: 50 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.5, y: 50 }}
            transition={{ type: "spring", damping: 15, stiffness: 200 }}
            className="mx-4 max-w-sm rounded-2xl bg-card p-8 text-center shadow-xl"
            onClick={(e) => e.stopPropagation()}
            onKeyDown={() => {}}
          >
            <motion.div
              animate={{ y: [0, -8, 0] }}
              transition={{ repeat: Number.POSITIVE_INFINITY, duration: 1.5 }}
              className="mb-4 text-6xl"
            >
              🛡️
            </motion.div>
            <p className="text-lg font-semibold">{message}</p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
