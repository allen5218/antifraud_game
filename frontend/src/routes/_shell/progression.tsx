import { createFileRoute, Link } from "@tanstack/react-router"
import {
  Coins,
  Compass,
  Hammer,
  Shield,
  Sparkles,
  Unlock,
  Zap,
} from "lucide-react"
import { useState } from "react"
import type { EquipmentItemPublic } from "@/client"
import { LongTermGrowth } from "@/components/progression/LongTermGrowth"
import { useEconomyMe } from "@/hooks/useEconomy"
import {
  useBreakthroughEquipment,
  useEquipment,
  useUpdateLoadout,
  useUpgradeEquipment,
} from "@/hooks/useEquipment"
import { useProgression, usePurchaseUnlock } from "@/hooks/useProgression"
import { formatMoney, isGreaterOrEqual } from "@/utils/money"
import { formatFactor } from "@/utils/progressionDisplay"

export const Route = createFileRoute("/_shell/progression")({
  component: ProgressionPage,
})

const FAMILY_LABELS: Record<string, string> = {
  save_vault: "防禦金庫",
  growth_lens: "經驗透鏡",
  forge_hammer: "鍛造神錘",
  balance_core: "平衡核心",
  streak_amplifier: "連勝擴大器",
  competition_crest: "競賽紋章",
}

const FAMILY_UNLOCK_INFO: Record<
  string,
  { label: string; desc: string; cost: bigint }
> = {
  growth_lens: {
    label: "經驗透鏡",
    desc: "提升養成經驗獲取倍率，每階提高 10%",
    cost: 100n,
  },
  forge_hammer: {
    label: "鍛造神錘",
    desc: "提升鍛造能量獲取倍率，每階提高 10%",
    cost: 300n,
  },
  balance_core: {
    label: "平衡核心",
    desc: "三通道共同加成，金錢/經驗/能量每階各提高 5%",
    cost: 800n,
  },
  streak_amplifier: {
    label: "連勝擴大器",
    desc: "當輪最佳連勝達 3 題以上時，三通道各額外提高 6%/階",
    cost: 2000n,
  },
  competition_crest: {
    label: "競賽紋章",
    desc: "提升每日訓練的當期養成競技積分，每階提高 10%",
    cost: 5000n,
  },
}

function ProgressionPage() {
  const progressionQuery = useProgression()
  const equipmentQuery = useEquipment()
  const { data: progression, isLoading: progLoading } = progressionQuery
  const { data: equipmentCatalog, isLoading: eqLoading } = equipmentQuery
  const { data: economy } = useEconomyMe()

  const updateLoadout = useUpdateLoadout()
  const upgradeItem = useUpgradeEquipment()
  const breakthroughItem = useBreakthroughEquipment()
  const purchaseUnlock = usePurchaseUnlock()

  const [activeFamilyFilter, setActiveFamilyFilter] = useState<string>("all")
  const [actionError, setActionError] = useState<string | null>(null)

  if (progressionQuery.isError || equipmentQuery.isError) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3 text-xs text-muted-foreground">
        <p>成長與裝備資料讀不到，請確認網路後再試一次。</p>
        <button
          type="button"
          onClick={() => {
            progressionQuery.refetch()
            equipmentQuery.refetch()
          }}
          className="rounded-lg bg-primary px-3 py-1.5 font-bold text-primary-foreground"
        >
          再試一次
        </button>
      </div>
    )
  }

  if (progLoading || eqLoading || !progression || !equipmentCatalog) {
    return (
      <div className="flex h-64 items-center justify-center text-xs text-muted-foreground">
        載入成長與裝備資料中…
      </div>
    )
  }

  const {
    core_level,
    growth_xp,
    next_level_xp,
    growth_progress_percent,
    forge_energy,
    max_active_slots,
    has_sixth_slot_license,
    blueprint_fragments,
    factors,
    next_objective,
  } = progression

  const { items } = equipmentCatalog
  const active_loadout = items
    .filter((it: EquipmentItemPublic) => it.is_equipped)
    .sort(
      (a: EquipmentItemPublic, b: EquipmentItemPublic) =>
        (a.slot_index ?? 0) - (b.slot_index ?? 0),
    )
  const inventory = items

  const userCash = economy?.cash ?? 0
  const equippedIds = new Set(
    active_loadout.map((item: EquipmentItemPublic) => item.id),
  )
  const ownedFamilies = new Set(
    inventory.map((item: EquipmentItemPublic) => item.family),
  )
  const unownedUnlockables = Object.entries(FAMILY_UNLOCK_INFO).filter(
    ([fam]) => !ownedFamilies.has(fam),
  )

  const handleEquip = (item: EquipmentItemPublic) => {
    setActionError(null)
    if (active_loadout.length >= max_active_slots) {
      setActionError(
        `生效槽位已滿（上限 ${max_active_slots} 槽），請先卸下其他工具。`,
      )
      return
    }
    const sameFamily = active_loadout.find(
      (it: EquipmentItemPublic) => it.family === item.family,
    )
    if (sameFamily) {
      setActionError(
        `同家族工具「${FAMILY_LABELS[item.family] ?? item.family}」只能裝備一件。`,
      )
      return
    }
    const newIds = [
      ...active_loadout.map((it: EquipmentItemPublic) => it.id),
      item.id,
    ]
    updateLoadout.mutate(newIds, {
      onError: () => setActionError("更新配裝失敗，請重試。"),
    })
  }

  const handleUnequip = (itemId: string) => {
    setActionError(null)
    const newIds = active_loadout
      .filter((it: EquipmentItemPublic) => it.id !== itemId)
      .map((it: EquipmentItemPublic) => it.id)
    updateLoadout.mutate(newIds, {
      onError: () => setActionError("卸下裝備失敗，請重試。"),
    })
  }

  const handleUpgrade = (item: EquipmentItemPublic) => {
    setActionError(null)
    if (!item.upgrade_cost_cash) return
    if (!isGreaterOrEqual(userCash, item.upgrade_cost_cash)) {
      setActionError("現金餘額不足，無法強化此工具。")
      return
    }
    upgradeItem.mutate(item, {
      onError: () => setActionError("強化失敗，請確認資源與網路狀態。"),
    })
  }

  const handleBreakthrough = (item: EquipmentItemPublic) => {
    setActionError(null)
    if (
      !item.breakthrough_ticket_cost &&
      blueprint_fragments < (item.breakthrough_cost_blueprints ?? 10)
    ) {
      setActionError("圖紙碎片不足 10 片，無法突破上限。")
      return
    }
    if (BigInt(forge_energy) < 500n) {
      setActionError("鍛造能量不足 500 點，無法突破上限。")
      return
    }
    breakthroughItem.mutate(item, {
      onError: () => setActionError("突破上限失敗，請重試。"),
    })
  }

  const handleUnlock6thSlot = () => {
    setActionError(null)
    if (core_level < 25) {
      setActionError("核心等級未達 25 級，還不能買額外槽位。")
      return
    }
    if (blueprint_fragments < 40) {
      setActionError("槽位圖紙不足 40 片，還不能買額外槽位。")
      return
    }
    purchaseUnlock.mutate("sixth_slot_license", {
      onError: () => setActionError("購買額外槽位失敗，請重試。"),
    })
  }

  const handleUnlockFamily = (familyKey: string, cost: bigint) => {
    setActionError(null)
    if (BigInt(forge_energy) < cost) {
      setActionError(`鍛造能量不足（需要 ${cost} 點能量）。`)
      return
    }
    purchaseUnlock.mutate(familyKey, {
      onError: () => setActionError("解鎖工具家族失敗，請重試。"),
    })
  }

  const filteredInventory =
    activeFamilyFilter === "all"
      ? inventory
      : inventory.filter(
          (item: EquipmentItemPublic) => item.family === activeFamilyFilter,
        )

  const xpPercent = Math.min(100, Math.max(0, growth_progress_percent ?? 0))

  return (
    <div className="flex flex-col gap-4 pb-12">
      <Link
        to="/quick/quiz"
        className="rounded-xl bg-primary p-3 text-center text-sm font-bold text-primary-foreground"
      >
        繼續訓練，賺取養成資源
      </Link>
      {/* 頂部核心能力卡 */}
      <div className="rounded-2xl border border-border bg-card p-4 text-card-foreground shadow-xs">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-1.5 text-xs font-bold text-muted-foreground">
              <Sparkles className="size-4 text-primary" aria-hidden="true" />
              核心養成階級
            </div>
            <div className="mt-0.5 text-2xl font-black text-foreground">
              Lv.{core_level}
            </div>
          </div>
          <div className="flex flex-col items-end gap-1">
            <span className="flex items-center gap-1 text-xs font-bold text-warning">
              <Hammer className="size-3.5" aria-hidden="true" />
              能量: {formatMoney(forge_energy)}
            </span>
            <span className="flex items-center gap-1 text-xs font-bold text-primary">
              <Zap className="size-3.5" aria-hidden="true" />
              圖紙: {blueprint_fragments} 片
            </span>
          </div>
        </div>

        {/* 經驗條 */}
        <div className="mt-3">
          <div className="flex justify-between text-[11px] text-muted-foreground">
            <span>本級進度 {xpPercent}%</span>
            <span>本級所需：{formatMoney(next_level_xp)}</span>
          </div>
          <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${xpPercent}%` }}
            />
          </div>
        </div>

        {/* 三通道倍率卡 */}
        <p className="mt-2 text-xs text-muted-foreground">
          累積養成經驗 {formatMoney(growth_xp)} · 突破圖紙{" "}
          {progression.breakthrough_blueprints} 張
        </p>
        <div className="mt-4 grid grid-cols-3 gap-2">
          <div className="rounded-xl bg-muted/60 p-2.5 text-center">
            <div className="text-[10px] text-muted-foreground">金錢產出</div>
            <div className="text-base font-extrabold text-legit">
              {formatFactor(factors?.cash)} 倍
            </div>
          </div>
          <div className="rounded-xl bg-muted/60 p-2.5 text-center">
            <div className="text-[10px] text-muted-foreground">養成經驗</div>
            <div className="text-base font-extrabold text-primary">
              {formatFactor(factors?.growth_xp)} 倍
            </div>
          </div>
          <div className="rounded-xl bg-muted/60 p-2.5 text-center">
            <div className="text-[10px] text-muted-foreground">鍛造能量</div>
            <div className="text-base font-extrabold text-warning">
              {formatFactor(factors?.energy)} 倍
            </div>
          </div>
        </div>

        <div className="mt-3 rounded-xl border border-primary/25 bg-surface-2 p-2.5 text-left text-xs">
          <div className="font-bold text-foreground">
            {next_objective ??
              `繼續累積養成經驗，下一級所需 ${formatMoney(next_level_xp)} 養成經驗。`}
          </div>
          <div className="mt-1 text-[11px] text-muted-foreground">
            裝備與強化會影響下次開局的收益，已開的這一局維持原倍率。
          </div>
        </div>
      </div>

      {/* 錯誤提示 */}
      {actionError && (
        <div
          role="alert"
          className="rounded-xl border border-destructive/40 bg-destructive/10 px-3.5 py-2.5 text-xs font-semibold text-destructive"
        >
          {actionError}
        </div>
      )}

      {/* 生效槽位裝備卡 */}
      <div className="rounded-2xl border border-border bg-card p-4 text-card-foreground shadow-xs">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold">生效配裝</h3>
            <p className="text-[11px] text-muted-foreground">
              容量 {active_loadout.length} / {max_active_slots}{" "}
              槽（同家族工具不可重複）
            </p>
          </div>
          {max_active_slots < 6 && (
            <div className="text-right">
              {core_level >= 25 && !has_sixth_slot_license ? (
                <button
                  type="button"
                  onClick={handleUnlock6thSlot}
                  disabled={
                    purchaseUnlock.isPending || blueprint_fragments < 40
                  }
                  className="rounded-lg bg-primary px-2.5 py-1 text-xs font-bold text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  多一個槽位（40 圖紙）
                </button>
              ) : (
                <span className="text-[11px] text-muted-foreground">
                  {core_level < 10
                    ? "下個槽位於 Lv.10"
                    : core_level < 25
                      ? "下個槽位於 Lv.25"
                      : core_level < 45
                        ? "下個槽位於 Lv.45"
                        : "已解鎖滿槽"}
                </span>
              )}
            </div>
          )}
        </div>

        {/* 槽位列表 */}
        <div className="mt-3 flex flex-col gap-2">
          {Array.from({ length: max_active_slots }).map((_, idx) => {
            const item = active_loadout[idx]
            if (!item) {
              return (
                <div
                  key={`empty-${idx}`}
                  className="flex items-center justify-between rounded-xl border border-dashed border-border p-3 text-xs text-muted-foreground"
                >
                  <span className="flex items-center gap-1.5">
                    <Shield className="size-4 opacity-40" />
                    空槽位 #{idx + 1}
                  </span>
                  <span className="text-[10px]">可從下方背包選擇工具裝備</span>
                </div>
              )
            }
            return (
              <div
                key={item.id}
                className="flex items-center justify-between rounded-xl border border-border bg-surface-2 p-3 text-xs"
              >
                <div className="flex flex-col">
                  <div className="flex items-center gap-1.5 font-bold">
                    <span>{FAMILY_LABELS[item.family] ?? item.name}</span>
                    <span className="rounded-md bg-primary/20 px-1.5 py-0.5 text-[10px] text-primary">
                      階級 {item.rank}
                    </span>
                  </div>
                  <div className="mt-0.5 text-[10px] text-muted-foreground">
                    {item.description}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleUnequip(item.id)}
                  className="rounded-lg bg-muted px-2.5 py-1 font-semibold text-muted-foreground hover:bg-destructive/20 hover:text-destructive"
                >
                  卸下
                </button>
              </div>
            )
          })}
        </div>
      </div>

      {/* 解鎖其他工具家族 */}
      {unownedUnlockables.length > 0 && (
        <div className="rounded-2xl border border-border bg-card p-4 text-card-foreground shadow-xs">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold flex items-center gap-1.5">
              <Compass className="size-4 text-primary" aria-hidden="true" />
              解鎖新工具家族
            </h3>
            <span className="text-xs text-muted-foreground">
              消耗鍛造能量解鎖
            </span>
          </div>
          <div className="mt-3 flex flex-col gap-2.5">
            {unownedUnlockables.map(([famKey, info]) => {
              const energyBig = BigInt(forge_energy)
              const canAfford = energyBig >= info.cost
              const energyGap = canAfford ? 0n : info.cost - energyBig
              return (
                <div
                  key={famKey}
                  className="flex items-center justify-between rounded-xl border border-border bg-muted/20 p-3 text-xs"
                >
                  <div className="flex flex-col">
                    <span className="font-bold text-foreground">
                      {info.label}
                    </span>
                    <span className="mt-0.5 text-[10px] text-muted-foreground">
                      {info.desc}
                    </span>
                    {!canAfford && (
                      <span className="mt-0.5 text-[10px] text-warning">
                        還差 {energyGap.toString()} 能量
                      </span>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleUnlockFamily(famKey, info.cost)}
                    disabled={!canAfford || purchaseUnlock.isPending}
                    className="flex items-center gap-1 rounded-lg bg-warning/20 px-2.5 py-1 text-xs font-bold text-warning hover:bg-warning/30 disabled:opacity-40"
                  >
                    <Hammer className="size-3" />
                    解鎖 ({info.cost.toString()} 能量)
                  </button>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 背包與工具升級 */}
      <div className="rounded-2xl border border-border bg-card p-4 text-card-foreground shadow-xs">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold">工具背包</h3>
          <span className="text-xs text-muted-foreground">
            共 {inventory.length} 件
          </span>
        </div>

        {/* 家族篩選器 */}
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={() => setActiveFamilyFilter("all")}
            className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${
              activeFamilyFilter === "all"
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground"
            }`}
          >
            全部
          </button>
          {Object.entries(FAMILY_LABELS).map(([famKey, famLabel]) => (
            <button
              key={famKey}
              type="button"
              onClick={() => setActiveFamilyFilter(famKey)}
              className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${
                activeFamilyFilter === famKey
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              {famLabel}
            </button>
          ))}
        </div>

        {/* 道具卡片清單 */}
        <div className="mt-3 flex flex-col gap-2.5">
          {filteredInventory.map((item: EquipmentItemPublic) => {
            const isEquipped = equippedIds.has(item.id)
            const canUpgrade = item.can_upgrade && item.upgrade_cost_cash
            const canAffordUpgrade =
              canUpgrade && item.upgrade_cost_cash
                ? isGreaterOrEqual(userCash, item.upgrade_cost_cash)
                : false
            const upgradeCashGap =
              canUpgrade && item.upgrade_cost_cash && !canAffordUpgrade
                ? BigInt(item.upgrade_cost_cash) - BigInt(userCash)
                : 0n
            const needsBreakthrough = item.can_breakthrough
            const reqBp = item.breakthrough_cost_blueprints ?? 10
            const hasEnoughBpForBt =
              Boolean(item.breakthrough_ticket_cost) ||
              blueprint_fragments >= reqBp
            const hasEnoughEnergyForBt = BigInt(forge_energy) >= 500n
            const canAffordBt = hasEnoughBpForBt && hasEnoughEnergyForBt
            const sameFamilyEquipped = active_loadout.some(
              (it: EquipmentItemPublic) =>
                it.family === item.family && it.id !== item.id,
            )
            const slotFull = active_loadout.length >= max_active_slots

            return (
              <div
                key={item.id}
                className="flex flex-col gap-2 rounded-xl border border-border bg-muted/30 p-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-bold text-foreground">
                      {FAMILY_LABELS[item.family] ?? item.name}
                    </span>
                    <span className="rounded-md bg-muted px-1.5 py-0.5 text-[10px] font-semibold text-muted-foreground">
                      階級 {item.rank} / {item.rank_cap}
                    </span>
                  </div>
                  {isEquipped ? (
                    <span className="rounded-md bg-legit/15 px-2 py-0.5 text-[10px] font-bold text-legit">
                      生效中
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={() => handleEquip(item)}
                      disabled={slotFull || sameFamilyEquipped}
                      className="rounded-lg bg-primary px-2.5 py-1 text-xs font-bold text-primary-foreground disabled:opacity-40"
                    >
                      {sameFamilyEquipped
                        ? "同家族已裝備"
                        : slotFull
                          ? "槽位已滿"
                          : "裝備"}
                    </button>
                  )}
                </div>

                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <div>{item.description}</div>
                </div>

                {/* 操作列：強化與突破 */}
                <div className="mt-1 flex flex-wrap items-center justify-end gap-2 border-t border-border/50 pt-2 text-xs">
                  {canUpgrade && item.upgrade_cost_cash && (
                    <div className="flex items-center gap-2">
                      {!canAffordUpgrade && upgradeCashGap > 0n && (
                        <span className="text-[10px] text-muted-foreground">
                          還差 ${formatMoney(upgradeCashGap)}
                        </span>
                      )}
                      <button
                        type="button"
                        onClick={() => handleUpgrade(item)}
                        disabled={!canAffordUpgrade || upgradeItem.isPending}
                        className="flex items-center gap-1 rounded-lg bg-surface-3 px-2.5 py-1 text-xs font-semibold hover:bg-surface-2 disabled:opacity-40"
                      >
                        <Coins className="size-3 text-legit" />
                        強化 (${formatMoney(item.upgrade_cost_cash)})
                      </button>
                    </div>
                  )}
                  {needsBreakthrough && (
                    <div className="flex items-center gap-2">
                      {!canAffordBt && (
                        <span className="text-[10px] text-muted-foreground">
                          {!hasEnoughBpForBt
                            ? `還差 ${reqBp - blueprint_fragments} 片圖紙`
                            : `還差 ${(500n - BigInt(forge_energy)).toString()} 能量`}
                        </span>
                      )}
                      <button
                        type="button"
                        onClick={() => handleBreakthrough(item)}
                        disabled={!canAffordBt || breakthroughItem.isPending}
                        className="flex items-center gap-1 rounded-lg bg-warning/20 px-2.5 py-1 text-xs font-bold text-warning hover:bg-warning/30 disabled:opacity-40"
                      >
                        <Unlock className="size-3" />
                        上限提高至 {item.rank_cap + 1} 階（
                        {item.breakthrough_ticket_cost
                          ? "1 張突破圖紙"
                          : "10 片槽位圖紙"}
                        與 500 能量）
                      </button>
                    </div>
                  )}
                  {!canUpgrade &&
                    !needsBreakthrough &&
                    item.rank >= item.rank_cap && (
                      <span className="text-[11px] text-muted-foreground">
                        已達目前最高階級
                      </span>
                    )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
      <LongTermGrowth />
    </div>
  )
}
