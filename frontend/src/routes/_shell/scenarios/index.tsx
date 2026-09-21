import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { HeartHandshake, MessageSquare, ShoppingBag } from "lucide-react"
import { useState } from "react"
import { InboxList } from "@/components/scenario/InboxList"
import {
  useContacts,
  usePurchaseItem,
  useScenarioInbox,
  useShopItems,
} from "@/hooks/useScenario"

export const Route = createFileRoute("/_shell/scenarios/")({
  component: ScenariosInboxPage,
})

function ScenariosInboxPage() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<"chats" | "items" | "contacts">(
    "chats",
  )
  const {
    data: inboxData,
    isPending: inboxPending,
    isError: inboxError,
  } = useScenarioInbox()
  const { data: contactsData } = useContacts()
  const { data: shopData } = useShopItems()
  const purchaseM = usePurchaseItem()

  return (
    <div className="flex flex-col space-y-3 p-1">
      {/* 頂部模式切換：聊天、物品、關係 */}
      <div className="flex rounded-xl bg-slate-900 border border-white/10 p-1">
        <button
          type="button"
          onClick={() => setActiveTab("chats")}
          data-testid="tab-chats-view"
          className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 text-xs font-bold rounded-lg transition-all ${
            activeTab === "chats"
              ? "bg-sky-600 text-white shadow-sm"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <MessageSquare className="size-3.5" />
          <span>聊天列表</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("items")}
          data-testid="tab-items-view"
          className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 text-xs font-bold rounded-lg transition-all ${
            activeTab === "items"
              ? "bg-sky-600 text-white shadow-sm"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <ShoppingBag className="size-3.5" />
          <span>物品商店</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("contacts")}
          data-testid="tab-contacts-view"
          className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 text-xs font-bold rounded-lg transition-all ${
            activeTab === "contacts"
              ? "bg-sky-600 text-white shadow-sm"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <HeartHandshake className="size-3.5" />
          <span>人物關係</span>
        </button>
      </div>

      {/* 1. 聊天列表頁 */}
      {activeTab === "chats" && (
        <div className="space-y-2">
          <div className="flex items-center justify-between px-1">
            <span className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              聯絡人事件對話
            </span>
          </div>
          {inboxPending ? (
            <p className="py-12 text-center text-xs text-muted-foreground">
              載入中…
            </p>
          ) : inboxError || !inboxData ? (
            <p className="py-12 text-center text-xs text-muted-foreground">
              載入失敗，請稍後再試
            </p>
          ) : (
            <InboxList
              items={inboxData}
              onOpen={(item) =>
                navigate({
                  to: "/scenarios/$scenarioId",
                  params: { scenarioId: item.id },
                })
              }
            />
          )}
        </div>
      )}

      {/* 2. 物品商店頁 (C5) */}
      {activeTab === "items" && (
        <div className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <span className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              防詐調查與社交道具（12件）
            </span>
            <span className="text-xs font-bold text-amber-300">
              餘額：${shopData?.user_cash?.toLocaleString() ?? 0}
            </span>
          </div>

          <div className="grid gap-2.5">
            {shopData?.items?.map((item) => {
              const isOwned = (item.owned_quantity ?? 0) > 0
              const canAfford = (shopData.user_cash ?? 0) >= item.price
              return (
                <div
                  key={item.id}
                  className="flex flex-col gap-2 rounded-2xl border border-white/10 bg-slate-900/90 p-3.5 shadow-sm"
                  data-testid={`shop-item-${item.id}`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-bold text-white">
                          {item.name}
                        </span>
                        {item.triggers_action && (
                          <span className="rounded bg-sky-500/20 px-1.5 py-0.5 text-[10px] font-bold text-sky-400">
                            觸發支線/工具
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-xs text-slate-300">
                        {item.description}
                      </p>
                      <p className="mt-1 text-[11px] text-slate-400">
                        用途：{item.visible_use}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between border-t border-white/5 pt-2">
                    <span className="text-xs font-mono font-bold text-amber-400">
                      ${item.price.toLocaleString()} 遊戲幣
                    </span>
                    <button
                      type="button"
                      disabled={isOwned || !canAfford || purchaseM.isPending}
                      onClick={() => purchaseM.mutate(item.id)}
                      className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-all ${
                        isOwned
                          ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                          : canAfford
                            ? "bg-amber-500 text-slate-950 hover:bg-amber-400 font-bold"
                            : "bg-slate-800 text-slate-500 cursor-not-allowed"
                      }`}
                    >
                      {isOwned ? "已持有" : canAfford ? "購買" : "餘額不足"}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 3. 人物關係記憶頁 (C4) */}
      {activeTab === "contacts" && (
        <div className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <span className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              聯絡人牽絆與事件記憶
            </span>
          </div>

          <div className="grid gap-2.5">
            {contactsData?.map((c) => (
              <div
                key={c.contact_id}
                className="flex flex-col gap-2 rounded-2xl border border-white/10 bg-slate-900/90 p-3.5 shadow-sm"
                data-testid={`contact-card-${c.contact_id}`}
              >
                <div className="flex items-center gap-3">
                  <span className="flex size-10 items-center justify-center rounded-full bg-slate-800 text-lg font-bold text-sky-400">
                    {c.avatar}
                  </span>
                  <div className="min-w-0 flex-1">
                    <span className="text-sm font-bold text-white">
                      {c.name}
                    </span>
                    <p className="text-xs text-slate-400 truncate">
                      {c.persona_desc}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 border-t border-white/5 pt-2">
                  <div className="rounded-lg bg-slate-950/60 p-2 text-center">
                    <span className="text-[10px] text-slate-400">
                      信任值 (Trust)
                    </span>
                    <p className="text-sm font-bold text-emerald-400">
                      {c.trust} / 100
                    </p>
                  </div>
                  <div className="rounded-lg bg-slate-950/60 p-2 text-center">
                    <span className="text-[10px] text-slate-400">
                      可靠度 (Reliability)
                    </span>
                    <p className="text-sm font-bold text-sky-400">
                      {c.reliability} / 100
                    </p>
                  </div>
                </div>

                {c.event_flags && c.event_flags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {c.event_flags.map((flag) => (
                      <span
                        key={flag}
                        className="rounded-md bg-white/10 px-2 py-0.5 text-[10px] font-semibold text-slate-300"
                      >
                        {flag === "respects_privacy"
                          ? "尊重隱私"
                          : flag === "evidence_grounded"
                            ? "依據充分"
                            : flag === "rash_accusation"
                              ? "曾草率指責"
                              : flag === "kept_promise"
                                ? "完成承諾"
                                : flag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
