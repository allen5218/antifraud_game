import { motion } from "framer-motion"
import { useEffect, useState } from "react"
import { MascotService } from "@/client"

interface EquippedItem {
  name: string
  category: string
}

export function MascotDisplay() {
  const [equipped, setEquipped] = useState<EquippedItem[]>([])

  useEffect(() => {
    MascotService.getMyMascot()
      .then((data: any) => {
        setEquipped(data.equipped_items ?? [])
      })
      .catch(() => {})
  }, [])

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", damping: 12, stiffness: 120 }}
      className="flex flex-col items-center"
    >
      <motion.div
        animate={{ y: [0, -6, 0] }}
        transition={{
          repeat: Number.POSITIVE_INFINITY,
          duration: 2.5,
          ease: "easeInOut",
        }}
        className="relative text-8xl"
      >
        🛡️
        {equipped.length > 0 && (
          <span className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
            {equipped.length}
          </span>
        )}
      </motion.div>
      {equipped.length > 0 && (
        <div className="mt-3 flex flex-wrap justify-center gap-1">
          {equipped.map((item) => (
            <span
              key={item.name}
              className="rounded-full bg-accent px-2 py-0.5 text-xs text-muted-foreground"
            >
              {item.name}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  )
}
