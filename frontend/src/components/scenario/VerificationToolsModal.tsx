import type { ScenarioEvidenceItem, ScenarioToolItem } from "@/client"
import { Button } from "@/components/ui/button"

interface VerificationToolsModalProps {
  open: boolean
  onClose: () => void
  tools: ScenarioToolItem[]
  unlockedEvidence: ScenarioEvidenceItem[]
  onVerify: (toolId: string) => void
  isVerifying: boolean
}

export function VerificationToolsModal({
  open,
  onClose,
  tools,
  unlockedEvidence,
  onVerify,
  isVerifying,
}: VerificationToolsModalProps) {
  if (!open) return null

  const unlockedToolIds = new Set(unlockedEvidence.map((e) => e.tool_id))

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 sm:items-center sm:p-4">
      <div className="flex max-h-[85vh] w-full max-w-lg flex-col rounded-t-2xl bg-background p-4 sm:rounded-2xl">
        <div className="flex items-center justify-between border-b pb-3">
          <div>
            <h3 className="text-base font-bold">🔍 獨立事實查證中心</h3>
            <p className="text-xs text-muted-foreground">
              不透過對方提供的連結，主動使用客觀公開管道查對真相
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1 text-muted-foreground hover:bg-muted"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-3 space-y-4">
          {/* 工具列表 */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              可用查證工具（點擊立即核實）
            </h4>
            <div className="grid gap-2">
              {tools.map((t) => {
                const isDone = unlockedToolIds.has(t.tool_id)
                return (
                  <div
                    key={t.tool_id}
                    className={`flex items-center justify-between gap-3 rounded-xl border p-3 text-left transition-colors ${
                      isDone
                        ? "border-green-300 bg-green-50/40 dark:border-green-950 dark:bg-green-950/20"
                        : "border-border bg-card"
                    }`}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-foreground">
                          {t.name}
                        </span>
                        {isDone && (
                          <span className="rounded bg-green-100 px-1.5 py-0.2 text-[10px] font-bold text-green-700 dark:bg-green-950 dark:text-green-300">
                            已查證
                          </span>
                        )}
                      </div>
                      <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">
                        {t.description}
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant={isDone ? "outline" : "default"}
                      disabled={isVerifying}
                      onClick={() => onVerify(t.tool_id)}
                      className="shrink-0 text-xs"
                    >
                      {isDone ? "重新查閱" : "執行查證"}
                    </Button>
                  </div>
                )
              })}
            </div>
          </div>

          {/* 已解鎖客觀事實 */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                查證事實報告 ({unlockedEvidence.length})
              </h4>
              {unlockedEvidence.length > 0 && (
                <span className="text-[11px] font-semibold text-green-600">
                  ✓ 已解鎖勝出全額獎勵與章節推進
                </span>
              )}
            </div>

            {unlockedEvidence.length === 0 ? (
              <div className="rounded-xl border border-dashed p-4 text-center text-xs text-muted-foreground">
                尚未執行任何查證。建議在下判斷前，先利用上方工具核驗事實，防範盲猜被扣除高額獎勵。
              </div>
            ) : (
              <div className="grid gap-2">
                {unlockedEvidence.map((ev) => (
                  <div
                    key={ev.tool_id}
                    className="rounded-xl border border-primary/20 bg-primary/5 p-3 text-xs leading-relaxed"
                  >
                    <div className="font-bold text-primary">📌 {ev.title}</div>
                    <p className="mt-1 text-foreground/90">{ev.content}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="border-t pt-3">
          <Button onClick={onClose} className="w-full text-xs font-bold">
            返回對話
          </Button>
        </div>
      </div>
    </div>
  )
}
