import { useQuery } from "@tanstack/react-query"
import { Building2, Sparkles, User, X } from "lucide-react"
import { PlayersService } from "@/client"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog"

interface PlayerShowcaseModalProps {
  playerId: string | null
  onClose: () => void
}

export function PlayerShowcaseModal({
  playerId,
  onClose,
}: PlayerShowcaseModalProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["player", "showcase", playerId],
    queryFn: () => PlayersService.getPlayerShowcase({ playerId: playerId! }),
    enabled: Boolean(playerId),
  })

  if (!playerId) return null

  const showcase = data

  return (
    <Dialog
      open={Boolean(playerId)}
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      <DialogContent
        showCloseButton={false}
        className="max-h-[85dvh] overflow-y-auto bg-card p-0 sm:max-w-sm"
      >
        <div className="w-full p-4 text-card-foreground">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <div className="flex items-center gap-2">
              <div className="flex size-8 items-center justify-center rounded-full bg-primary/20 text-primary">
                <User className="size-4" />
              </div>
              <div>
                <DialogTitle className="text-sm font-bold">
                  {showcase?.nickname ?? "玩家名片"}
                </DialogTitle>
                <DialogDescription className="text-xs">
                  公開裝備與養成成果
                </DialogDescription>
              </div>
            </div>
            <button
              type="button"
              aria-label="關閉玩家名片"
              onClick={onClose}
              className="rounded-lg p-1 text-muted-foreground hover:bg-muted"
            >
              <X className="size-4" />
            </button>
          </div>

          {isError ? (
            <p role="alert" className="py-6 text-center text-sm text-scam">
              玩家名片載入失敗。
            </p>
          ) : isLoading || !showcase ? (
            <div className="py-8 text-center text-xs text-muted-foreground">
              載入名片中…
            </div>
          ) : (
            <div className="mt-3 flex flex-col gap-3">
              {showcase.title && (
                <p className="font-bold text-warning">{showcase.title}</p>
              )}
              {(showcase.collectibles ?? []).map((item) => (
                <p
                  key={item.item_key}
                  className="text-xs text-muted-foreground"
                >
                  {item.name}
                </p>
              ))}
              <div className="flex items-center justify-between rounded-xl bg-surface-2 p-3">
                <span className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
                  <Sparkles className="size-3.5 text-primary" />
                  信譽
                </span>
                <span className="text-base font-extrabold text-foreground">
                  {showcase.reputation ?? 0} 點
                </span>
              </div>
              {showcase.top_industry && (
                <div className="flex items-center justify-between rounded-xl bg-surface-2 p-3">
                  <span className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
                    <Building2 className="size-3.5 text-primary" />
                    最好的房產
                  </span>
                  <span className="text-base font-extrabold text-foreground">
                    {showcase.top_industry}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
