import { motion } from "framer-motion"

interface MascotPreviewProps {
  equippedItems: { name: string; image_url: string }[]
}

export function MascotPreview({ equippedItems }: MascotPreviewProps) {
  return (
    <div className="flex flex-col items-center rounded-xl border bg-card p-6 shadow-sm">
      <h3 className="mb-4 text-sm font-medium text-muted-foreground">
        吉祥物預覽
      </h3>
      <motion.img
        src="/assets/mascot/base.webp"
        alt="防詐小衛士"
        width={112}
        height={112}
        animate={{ y: [0, -6, 0] }}
        transition={{
          repeat: Number.POSITIVE_INFINITY,
          duration: 2.5,
          ease: "easeInOut",
        }}
        className="size-28 rounded-3xl object-cover"
      />
      {equippedItems.length > 0 ? (
        <div className="mt-4 flex flex-wrap justify-center gap-2">
          {equippedItems.map((item) => (
            <span
              key={item.name}
              className="flex items-center gap-1.5 rounded-full bg-primary/10 py-1 pr-3 pl-1 text-sm"
            >
              {item.image_url && (
                <img
                  src={item.image_url}
                  alt=""
                  aria-hidden="true"
                  className="size-6 rounded-full object-cover"
                />
              )}
              {item.name}
            </span>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm text-muted-foreground">還沒有裝備任何配件</p>
      )}
    </div>
  )
}
