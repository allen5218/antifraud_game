import { useQuery } from "@tanstack/react-query"
import { Shield, Sparkles, User, X } from "lucide-react"
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

const FAMILY_LABELS: Record<string, string> = {
  save_vault: "防禦金庫",
  growth_lens: "經驗透鏡",
  forge_hammer: "鍛造神錘",
  balance_core: "平衡核心",
  streak_amplifier: "連勝擴大器",
  competition_crest: "競賽紋章",
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
                  核心養成等級
                </span>
                <span className="text-base font-extrabold text-foreground">
                  Lv.{showcase.core_level}
                </span>
              </div>

              <div>
                <div className="mb-1.5 text-xs font-bold text-muted-foreground">
                  生效工具組合 ({showcase.active_loadout.length} 件)
                </div>
                {showcase.active_loadout.length === 0 ? (
                  <div className="rounded-xl border border-dashed border-border p-3 text-center text-xs text-muted-foreground">
                    尚未配戴任何生效工具
                  </div>
                ) : (
                  <div className="flex flex-col gap-1.5">
                    {showcase.active_loadout.map((item) => (
                      <div
                        key={item.item_id}
                        className="flex items-center justify-between rounded-xl border border-border bg-muted/40 p-2.5 text-xs"
                      >
                        <div>
                          <div className="flex items-center gap-1 font-bold">
                            <Shield className="size-3 text-primary" />
                            <span>
                              {FAMILY_LABELS[item.family] ?? item.name}
                            </span>
                            <span className="rounded bg-primary/20 px-1 py-0.5 text-[9px] text-primary">
                              {item.rank} 階
                            </span>
                          </div>
                          <div className="text-[10px] text-muted-foreground">
                            金錢 {item.factors.cash} 倍 · 養成經驗{" "}
                            {item.factors.growth_xp} 倍 · 能量{" "}
                            {item.factors.energy} 倍
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
