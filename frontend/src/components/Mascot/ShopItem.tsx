import { motion } from "framer-motion"

interface ShopItemProps {
  name: string
  category: string
  cost: number
  emoji: string
  owned: boolean
  equipped: boolean
  canAfford: boolean
  onPurchase: () => void
  onToggleEquip: () => void
}

export function ShopItem({
  name,
  category,
  cost,
  emoji,
  owned,
  equipped,
  canAfford,
  onPurchase,
  onToggleEquip,
}: ShopItemProps) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={`rounded-xl border-2 p-4 transition-colors ${
        equipped
          ? "border-primary bg-primary/5"
          : owned
            ? "border-green-500/30 bg-green-500/5"
            : "border-border bg-card"
      }`}
    >
      <div className="mb-3 text-center text-4xl">{emoji}</div>
      <h3 className="text-center text-sm font-semibold">{name}</h3>
      <p className="mb-3 text-center text-xs text-muted-foreground">
        {category}
      </p>

      {owned ? (
        <button
          type="button"
          onClick={onToggleEquip}
          className={`w-full rounded-lg py-2 text-sm font-medium transition-colors ${
            equipped
              ? "bg-primary text-primary-foreground"
              : "bg-accent text-foreground hover:bg-accent/80"
          }`}
        >
          {equipped ? "已裝備" : "裝備"}
        </button>
      ) : (
        <button
          type="button"
          onClick={onPurchase}
          disabled={!canAfford}
          className="w-full rounded-lg bg-primary py-2 text-sm font-medium text-primary-foreground transition-colors disabled:opacity-50"
        >
          {cost} 積分
        </button>
      )}
    </motion.div>
  )
}
