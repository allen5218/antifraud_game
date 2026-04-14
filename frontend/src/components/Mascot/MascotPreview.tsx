import { motion } from "framer-motion"

interface MascotPreviewProps {
  equippedItems: { name: string; emoji: string }[]
}

export function MascotPreview({ equippedItems }: MascotPreviewProps) {
  return (
    <div className="flex flex-col items-center rounded-xl border bg-card p-6 shadow-sm">
      <h3 className="mb-4 text-sm font-medium text-muted-foreground">
        吉祥物預覽
      </h3>
      <motion.div
        animate={{ y: [0, -6, 0] }}
        transition={{
          repeat: Number.POSITIVE_INFINITY,
          duration: 2.5,
          ease: "easeInOut",
        }}
        className="text-7xl"
      >
        🛡️
      </motion.div>
      {equippedItems.length > 0 ? (
        <div className="mt-4 flex flex-wrap justify-center gap-2">
          {equippedItems.map((item) => (
            <span
              key={item.name}
              className="rounded-full bg-primary/10 px-3 py-1 text-sm"
            >
              {item.emoji} {item.name}
            </span>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm text-muted-foreground">尚未裝備任何物品</p>
      )}
    </div>
  )
}
