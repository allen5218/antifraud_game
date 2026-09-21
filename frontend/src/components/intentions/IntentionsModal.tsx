import { ArrowRight, Brain, CheckCircle2, Shield, X, Zap } from "lucide-react"
import {
  useEquipCard,
  useIntentionsOverview,
  useUnequipCard,
} from "@/hooks/useIntentions"

interface IntentionsModalProps {
  isOpen: boolean
  onClose: () => void
}

export function IntentionsModal({ isOpen, onClose }: IntentionsModalProps) {
  const { data } = useIntentionsOverview()
  const equipMutation = useEquipCard()
  const unequipMutation = useUnequipCard()

  if (!isOpen) return null

  const equippedSlots = data?.equipped_slots ?? [null, null]
  const cards = data?.cards ?? []
  const bonuses = data?.bonuses ?? {
    total_brake_latency: 0,
    tag_mitigations: {},
    far_transfer_multiplier: 1.0,
    equipped_count: 0,
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md font-['Plus_Jakarta_Sans',sans-serif]">
      <div className="relative flex max-h-[90vh] w-full max-w-2xl flex-col rounded-3xl border border-white/20 bg-slate-900/95 p-6 shadow-2xl backdrop-blur-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/20 bg-white/10 shadow-[0_0_12px_rgba(255,255,255,0.1)]">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-wide">
                認知反射槽 (If-Then 執行意圖)
              </h2>
              <p className="text-xs text-slate-400">
                Gollwitzer 心理學：將抽象警語轉化為神經反射動作劇本
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-xl border border-white/10 p-2 text-slate-400 hover:bg-white/10 hover:text-white transition-colors cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Modal Scroll Body */}
        <div className="flex-1 overflow-y-auto py-4 space-y-5 pr-1 text-xs">
          {/* Active Equipment Slots Banner */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-300">
                已啟動之反射槽位 (Active Reflex Slots)
              </span>
              <span className="text-[10px] text-emerald-400 font-mono font-semibold">
                決策煞車冷靜：+{bonuses.total_brake_latency}秒 · 遠遷移：x
                {bonuses.far_transfer_multiplier}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[0, 1].map((slotIdx) => {
                const card = equippedSlots[slotIdx]
                return (
                  <div
                    key={slotIdx}
                    className={`rounded-2xl border p-3.5 transition-all ${
                      card
                        ? "border-emerald-500/40 bg-emerald-950/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]"
                        : "border-white/10 bg-white/5 border-dashed"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="rounded-md border border-white/20 bg-white/10 px-2 py-0.5 text-[10px] font-bold text-slate-200">
                        槽位 {slotIdx + 1}
                      </span>
                      {card && (
                        <button
                          onClick={() => unequipMutation.mutate(slotIdx)}
                          disabled={unequipMutation.isPending}
                          className="text-[10px] text-red-400 hover:text-red-300 font-bold transition-colors cursor-pointer"
                        >
                          卸下
                        </button>
                      )}
                    </div>

                    {card ? (
                      <div className="space-y-1.5">
                        <div className="font-bold text-white text-xs flex items-center gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                          <span>{card.name}</span>
                        </div>
                        <div className="rounded-lg bg-black/40 border border-white/5 p-2 font-mono text-[11px] leading-relaxed">
                          <span className="text-amber-300 block">
                            {card.if_trigger}
                          </span>
                          <span className="text-emerald-400 block mt-1">
                            {card.then_action}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-400 pt-0.5">
                          加成：{card.passive_bonus_text}
                        </p>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center py-5 text-slate-400">
                        <Brain className="w-6 h-6 mb-1 text-slate-500" />
                        <span className="text-[11px]">尚未裝備反射卡</span>
                        <span className="text-[10px] text-slate-400 mt-0.5">
                          點擊下方卡片裝備至此槽位
                        </span>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Cards Catalog */}
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-300">
                已解鎖之認知反射卡卷宗 (Available Reflex Cards)
              </span>
              <span className="text-[10px] text-slate-400">
                共 {cards.length} 張反射劇本
              </span>
            </div>

            <div className="grid gap-3">
              {cards.map((c) => (
                <div
                  key={c.id}
                  className={`rounded-2xl border p-4 transition-all ${
                    c.is_equipped
                      ? "border-emerald-500/50 bg-slate-900/90 shadow-[0_0_15px_rgba(16,185,129,0.08)]"
                      : "border-white/10 bg-white/5 hover:border-white/20"
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-2.5">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-xs">
                          {c.name}
                        </span>
                        <span className="rounded bg-white/10 px-1.5 py-0.5 text-[9px] font-semibold text-slate-300">
                          {c.title_label}
                        </span>
                        {c.is_equipped && (
                          <span className="rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-1.5 py-0.5 text-[9px] font-bold">
                            槽位 {(c.slot_index ?? 0) + 1} 啟動中
                          </span>
                        )}
                      </div>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        理論依據：{c.psychological_basis}
                      </p>
                    </div>

                    <div className="flex items-center gap-2 self-end sm:self-auto shrink-0">
                      <button
                        onClick={() =>
                          equipMutation.mutate({ cardId: c.id, slotIndex: 0 })
                        }
                        disabled={
                          equipMutation.isPending ||
                          (c.is_equipped && c.slot_index === 0)
                        }
                        className={`px-2.5 py-1 rounded-lg text-[10px] font-bold border transition-colors cursor-pointer ${
                          c.is_equipped && c.slot_index === 0
                            ? "border-emerald-500/40 bg-emerald-500/20 text-emerald-300"
                            : "border-white/15 bg-white/5 text-slate-300 hover:bg-white/15 hover:text-white"
                        }`}
                      >
                        {c.is_equipped && c.slot_index === 0
                          ? "槽位 1 運作中"
                          : "裝備槽位 1"}
                      </button>
                      <button
                        onClick={() =>
                          equipMutation.mutate({ cardId: c.id, slotIndex: 1 })
                        }
                        disabled={
                          equipMutation.isPending ||
                          (c.is_equipped && c.slot_index === 1)
                        }
                        className={`px-2.5 py-1 rounded-lg text-[10px] font-bold border transition-colors cursor-pointer ${
                          c.is_equipped && c.slot_index === 1
                            ? "border-emerald-500/40 bg-emerald-500/20 text-emerald-300"
                            : "border-white/15 bg-white/5 text-slate-300 hover:bg-white/15 hover:text-white"
                        }`}
                      >
                        {c.is_equipped && c.slot_index === 1
                          ? "槽位 2 運作中"
                          : "裝備槽位 2"}
                      </button>
                    </div>
                  </div>

                  {/* If-Then Body */}
                  <div className="mt-3 rounded-xl bg-black/40 border border-white/5 p-3 space-y-1.5 font-mono text-xs">
                    <div className="text-amber-300 flex items-start gap-1.5">
                      <ArrowRight className="w-3.5 h-3.5 text-amber-400 mt-0.5 shrink-0" />
                      <span>{c.if_trigger}</span>
                    </div>
                    <div className="text-emerald-400 flex items-start gap-1.5 border-t border-white/5 pt-1.5">
                      <Shield className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
                      <span>{c.then_action}</span>
                    </div>
                  </div>

                  <div className="mt-2 text-[10px] text-slate-300 font-mono">
                    加成屬性：{c.passive_bonus_text}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-white/10 pt-3 text-center text-[11px] text-slate-400">
          提示：裝備符合弱點標籤的反射卡，將在情境模擬中自動啟動冷靜緩衝並降低資產損失。
        </div>
      </div>
    </div>
  )
}
