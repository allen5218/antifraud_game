import {
  CheckCircle2,
  Coins,
  FileCheck2,
  Home,
  Lock,
  ShoppingBag,
  Users,
  Wrench,
  X,
  Zap,
} from "lucide-react"
import type { ComponentType } from "react"
import type { ScenarioBranchAction } from "@/client"

interface BranchActionsModalProps {
  open: boolean
  onClose: () => void
  actions: ScenarioBranchAction[]
  onExecute: (actionId: string) => void
  isExecuting: boolean
  onGoShop?: () => void
}

const CATEGORY_META: Record<
  string,
  { label: string; icon: ComponentType<{ className?: string }>; color: string }
> = {
  cash: {
    label: "資金調度",
    icon: Coins,
    color: "text-amber-400 bg-amber-500/10 border-amber-500/30",
  },
  network: {
    label: "人脈牽絆",
    icon: Users,
    color: "text-sky-400 bg-sky-500/10 border-sky-500/30",
  },
  handling: {
    label: "應對處置",
    icon: FileCheck2,
    color: "text-purple-400 bg-purple-500/10 border-purple-500/30",
  },
  property_vehicle: {
    label: "資產調度",
    icon: Home,
    color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
  },
  xp_item: {
    label: "調查裝備",
    icon: Wrench,
    color: "text-indigo-400 bg-indigo-500/10 border-indigo-500/30",
  },
}

export function BranchActionsModal({
  open,
  onClose,
  actions,
  onExecute,
  isExecuting,
  onGoShop,
}: BranchActionsModalProps) {
  if (!open) return null

  const availableCount = actions.filter((a) => a.available).length

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 backdrop-blur-sm p-0 sm:items-center sm:p-4">
      <div className="flex max-h-[85vh] w-full max-w-lg flex-col rounded-t-2xl bg-slate-900 border-[1.5px] border-white/25 p-4 sm:rounded-2xl glow-card overflow-hidden shadow-2xl">
        {/* 標題欄 */}
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div>
            <h3 className="flex items-center text-base font-bold text-white">
              <Zap className="size-4 text-emerald-400 mr-2" />
              <span>
                可以怎麼幫忙 ({availableCount}/{actions.length})
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              從你目前能做到的事情裡，選一個方法繼續處理
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1 text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="關閉"
          >
            <X className="size-5" />
          </button>
        </div>

        {/* 簡短提醒 */}
        <div className="mt-2.5 rounded-xl border border-emerald-500/30 bg-emerald-950/30 px-3 py-2 text-[11px] text-emerald-300 flex items-center gap-2">
          <FileCheck2 className="size-4 shrink-0 text-emerald-400" />
          <span>
            每個方法只提供一部分線索；文件、照片或裝備本身不會直接證明對方真偽。
          </span>
        </div>

        {/* 行動清單 */}
        <div className="flex-1 overflow-y-auto py-3 space-y-2.5">
          {actions.length === 0 ? (
            <p className="py-8 text-center text-xs text-slate-400">
              此情境目前無可用的分支行動
            </p>
          ) : (
            actions.map((act) => {
              const meta = CATEGORY_META[act.category] || {
                label: act.category,
                icon: Zap,
                color: "text-slate-400 bg-slate-800 border-slate-700",
              }
              const Icon = meta.icon

              return (
                <div
                  key={act.action_id}
                  data-testid={`branch-action-card-${act.action_id}`}
                  className={`rounded-2xl border-[1.5px] p-3.5 transition-all ${
                    act.available
                      ? "border-white/20 bg-slate-800/90 shadow-sm"
                      : "border-white/5 bg-slate-900/60 opacity-70"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span
                          className={`inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-bold border ${meta.color}`}
                        >
                          <Icon className="size-3" />
                          {meta.label}
                        </span>
                        <span className="text-xs font-bold text-white truncate">
                          {act.label}
                        </span>
                      </div>
                      <p className="mt-1.5 text-xs text-slate-300 leading-relaxed">
                        {act.description}
                      </p>
                    </div>
                  </div>

                  {/* 條件需求與執行按鈕 */}
                  <div className="mt-3 flex items-center justify-between border-t border-white/10 pt-2.5">
                    <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
                      {act.completed ? (
                        <span className="rounded bg-sky-500/20 px-1.5 py-0.5 text-sky-300 border border-sky-500/30">
                          本次已完成
                        </span>
                      ) : act.available ? (
                        <span className="rounded bg-emerald-500/20 px-1.5 py-0.5 text-emerald-300 border border-emerald-500/30">
                          狀態條件符合
                        </span>
                      ) : (
                        <span className="rounded bg-slate-800 px-1.5 py-0.5 text-slate-400 border border-slate-700">
                          條件尚未達成
                        </span>
                      )}
                    </div>

                    {act.completed ? (
                      <div className="flex items-center gap-1 text-[11px] text-sky-300 font-medium">
                        <CheckCircle2 className="size-3 shrink-0" />
                        <span>結果已寫入聊天紀錄</span>
                      </div>
                    ) : act.available ? (
                      <button
                        type="button"
                        disabled={isExecuting}
                        onClick={() => onExecute(act.action_id)}
                        data-testid={`execute-action-${act.action_id}`}
                        className="rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50 transition-all shadow-sm"
                      >
                        {isExecuting ? "執行中…" : "採取此行動"}
                      </button>
                    ) : (
                      <div className="flex items-center gap-1 text-[11px] text-rose-400 font-medium">
                        <Lock className="size-3 shrink-0" />
                        <span>{act.unavailable_reason || "條件未達成"}</span>
                      </div>
                    )}
                  </div>
                </div>
              )
            })
          )}
        </div>

        {/* 底部功能與前往商店捷徑 */}
        <div className="border-t border-white/10 pt-3 flex items-center justify-between gap-2">
          {onGoShop && (
            <button
              type="button"
              onClick={onGoShop}
              className="flex items-center gap-1 text-xs text-sky-400 hover:text-sky-300 font-medium"
            >
              <ShoppingBag className="size-3.5" />
              <span>前往防詐道具商店購置裝備 ›</span>
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            className="ml-auto rounded-lg bg-slate-800 px-4 py-1.5 text-xs font-bold text-white hover:bg-slate-700 border border-white/20"
          >
            返回對話
          </button>
        </div>
      </div>
    </div>
  )
}
