import { Trophy } from "lucide-react"
import { CollectionsService } from "@/client"
import { useCollections, useGameplayAction } from "@/hooks/useCollections"

/** 賽季拿到的獎盃、稱號、吉祥物外觀：選要擺進房間的獎盃、展示哪個稱號 */
export function Honors() {
  const { data, isError } = useCollections()
  const action = useGameplayAction()
  const disabled = action.isPending
  if (isError)
    return (
      <p role="alert" className="text-sm text-scam">
        榮譽載入失敗，請重新整理。
      </p>
    )
  if (!data) return null
  const configure = (type: "title" | "appearance" | "showcase", key: string) =>
    action.mutate(() =>
      CollectionsService.configureDisplay({
        action: type,
        requestBody: { key },
      }),
    )
  return (
    <section
      aria-label="榮譽"
      className="rounded-3xl border border-border bg-card p-4"
    >
      <h2 className="flex items-center gap-2 text-base font-bold">
        <Trophy aria-hidden className="size-5 text-warning" />
        榮譽
      </h2>
      {action.isError && (
        <p role="alert" className="mt-2 text-sm text-scam">
          沒有改成功，展示位置可能滿了，請先收起一件。
        </p>
      )}
      <p className="my-2 text-xs text-muted-foreground">
        房間裡擺了 {data.collectibles.filter((c) => c.displayed).length}／
        {data.showcase_capacity} 件
      </p>
      {data.collectibles.length === 0 && (
        <p className="text-sm text-muted-foreground">
          參加兩週競技榜，拿到的獎盃會放在這裡。
        </p>
      )}
      {data.collectibles.map((item) => (
        <div
          key={item.item_key}
          className="flex flex-wrap items-center justify-between gap-2 border-t border-border py-2 text-sm"
        >
          <span>{item.name}</span>
          <div className="flex gap-2">
            {item.kind === "pet_skin" && (
              <button
                type="button"
                disabled={disabled || data.active_appearance === item.item_key}
                className="rounded-lg bg-primary/15 px-3 py-2 text-xs text-primary"
                onClick={() => configure("appearance", item.item_key)}
              >
                {data.active_appearance === item.item_key
                  ? "外觀使用中"
                  : "套用吉祥物外觀"}
              </button>
            )}
            <button
              type="button"
              disabled={disabled}
              className="rounded-lg bg-surface-2 px-3 py-2 text-xs"
              onClick={() => configure("showcase", item.item_key)}
            >
              {item.displayed ? "收起來" : "擺進房間"}
            </button>
          </div>
        </div>
      ))}
      {data.titles.map((title) => (
        <button
          type="button"
          key={title.key}
          disabled={disabled || data.active_title === title.name}
          className="mt-3 mr-2 rounded-lg bg-warning/15 px-3 py-2 text-xs text-warning"
          onClick={() => configure("title", title.key)}
        >
          {data.active_title === title.name ? "展示中：" : "展示稱號："}
          {title.name}
        </button>
      ))}
    </section>
  )
}
