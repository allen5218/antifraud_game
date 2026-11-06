import { House, PawPrint, Save, Sparkles, Trophy } from "lucide-react"
import { useState } from "react"
import { CollectionsService, SeasonsService } from "@/client"
import { useCollections, useGameplayAction } from "@/hooks/useCollections"
import { useEconomyMe } from "@/hooks/useEconomy"
import { useEquipment } from "@/hooks/useEquipment"
import { useProgression } from "@/hooks/useProgression"
import { formatMoney } from "@/utils/money"

export function LongTermGrowth() {
  const { data, isError } = useCollections()
  const { data: equipment } = useEquipment()
  const { data: economy } = useEconomyMe()
  const { data: progression } = useProgression()
  const action = useGameplayAction()
  const [family, setFamily] = useState("save_vault")
  const disabled = action.isPending
  if (isError)
    return (
      <p role="alert" className="text-sm text-scam">
        長期養成載入失敗，請重新整理。
      </p>
    )
  if (!data)
    return <p className="text-sm text-muted-foreground">載入長期養成…</p>
  const userCash = BigInt(economy?.cash ?? 0)
  const userEnergy = BigInt(progression?.forge_energy ?? 0)
  const userBlueprints = progression?.blueprint_fragments ?? 0
  const configure = (
    type: "title" | "appearance" | "showcase" | "showcase_slot" | "preset_slot",
    key: string,
    level?: number,
  ) =>
    action.mutate(() =>
      CollectionsService.configureDisplay({
        action: type,
        requestBody: { key, expected_level: level },
      }),
    )
  return (
    <section className="flex flex-col gap-4" aria-label="長期養成與榮譽">
      <h2 className="text-lg font-bold">長期養成與榮譽</h2>
      <p className="text-xs text-muted-foreground">
        換期保留房屋建設、寵物羈絆、收藏與稱號。花錢不會降低累積所得。
      </p>
      <p className="text-sm font-semibold">
        累積訓練所得 ${formatMoney(data.lifetime_cash)}
      </p>
      {action.isError && (
        <p role="alert" className="text-sm text-scam">
          操作未完成，請確認資源、展示空位或最新進度後重試。
        </p>
      )}
      {(data.tool_choices ?? []).map((seasonId) => (
        <div
          key={seasonId}
          className="rounded-xl border border-primary bg-card p-3"
        >
          <h3 className="flex items-center gap-2 font-bold">
            <Trophy className="size-4" />
            冠軍六階工具可領取
          </h3>
          <label className="mt-2 block text-xs">
            選擇家族
            <select
              aria-label="冠軍工具家族"
              className="ml-2 rounded border border-border bg-background p-2"
              value={family}
              onChange={(e) => setFamily(e.target.value)}
            >
              {[
                ["save_vault", "儲金"],
                ["growth_lens", "成長"],
                ["forge_hammer", "鍛造"],
                ["balance_core", "均衡"],
                ["streak_amplifier", "連勝"],
                ["competition_crest", "競技"],
              ].map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            disabled={disabled}
            className="mt-2 rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground disabled:opacity-50"
            onClick={() =>
              action.mutate(() =>
                SeasonsService.claimChampionTool({
                  seasonId,
                  requestBody: { family },
                }),
              )
            }
          >
            領取冠軍工具
          </button>
        </div>
      ))}
      <div className="grid gap-3 sm:grid-cols-2">
        {data.assets.map((asset) => {
          const reqCash = BigInt(asset.cash_cost)
          const reqEnergy = BigInt(asset.energy_cost)
          const canAffordCash = userCash >= reqCash
          const canAffordEnergy = userEnergy >= reqEnergy
          const canAffordAsset = canAffordCash && canAffordEnergy
          const cashGap = canAffordCash ? 0n : reqCash - userCash
          const energyGap = canAffordEnergy ? 0n : reqEnergy - userEnergy
          return (
            <div
              key={`${asset.kind}:${asset.target_id}`}
              className="rounded-xl border border-border bg-card p-3"
            >
              <h3 className="flex items-center gap-2 font-bold">
                {asset.kind === "house" ? (
                  <House className="size-4" />
                ) : (
                  <PawPrint className="size-4" />
                )}
                {asset.name}{" "}
                <span className="text-xs text-muted-foreground">
                  {asset.level} 級
                </span>
              </h3>
              <p className="my-2 text-xs text-muted-foreground">
                {asset.kind === "house"
                  ? "建設累積房屋排行分數，不改原房租。"
                  : "展示中的寵物每級提高養成產出 1%，最高兩倍。"}
              </p>
              {!canAffordAsset && (
                <p className="mb-1.5 text-[11px] text-warning">
                  還差
                  {cashGap > 0n ? ` $${formatMoney(cashGap)} 現金` : ""}
                  {cashGap > 0n && energyGap > 0n ? "、" : ""}
                  {energyGap > 0n ? ` ${formatMoney(energyGap)} 能量` : ""}
                </p>
              )}
              <button
                type="button"
                disabled={disabled || !canAffordAsset}
                className="w-full rounded-lg bg-surface-2 p-2 text-xs font-semibold disabled:opacity-40"
                onClick={() =>
                  action.mutate(() =>
                    CollectionsService.upgradeCollection({
                      kind: asset.kind,
                      targetId: asset.target_id,
                      requestBody: {
                        key: crypto.randomUUID(),
                        expected_level: asset.level,
                      },
                    }),
                  )
                }
              >
                {asset.kind === "house" ? "建設" : "培養羈絆"} · $
                {formatMoney(asset.cash_cost, { abbreviated: true })} 與{" "}
                {formatMoney(asset.energy_cost)} 能量
              </button>
            </div>
          )
        })}
      </div>
      <div className="rounded-xl border border-border bg-card p-3">
        <h3 className="flex items-center gap-2 font-bold">
          <Trophy className="size-4" />
          房間展示櫃
        </h3>
        <p className="my-2 text-xs text-muted-foreground">
          {data.collectibles.filter((c) => c.displayed).length}／
          {data.showcase_capacity} 個展示位置。展示與生效裝備分開計算。
        </p>
        {data.collectibles.length === 0 && (
          <p className="text-xs text-muted-foreground">
            參與當期賽季，將成果永久帶回房間。
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
                  disabled={
                    disabled || data.active_appearance === item.item_key
                  }
                  className="rounded bg-primary/15 p-2 text-xs text-primary"
                  onClick={() => configure("appearance", item.item_key)}
                >
                  {data.active_appearance === item.item_key
                    ? "外觀使用中"
                    : "套用寵物外觀"}
                </button>
              )}
              <button
                type="button"
                disabled={disabled}
                className="rounded bg-surface-2 p-2 text-xs"
                onClick={() => configure("showcase", item.item_key)}
              >
                {item.displayed ? "收回背包" : "放進房間"}
              </button>
            </div>
          </div>
        ))}
        {data.showcase_capacity < 6 && (
          <button
            type="button"
            disabled={disabled || userBlueprints < 10}
            className="mt-3 rounded-lg bg-surface-2 p-2 text-xs disabled:opacity-40"
            onClick={() =>
              configure(
                "showcase_slot",
                crypto.randomUUID(),
                data.showcase_capacity,
              )
            }
          >
            10 片圖紙增加展示位置
            {userBlueprints < 10 ? `（還差 ${10 - userBlueprints} 片）` : ""}
          </button>
        )}
        {data.titles.map((title) => (
          <button
            type="button"
            key={title.key}
            disabled={disabled || data.active_title === title.name}
            className="mt-3 mr-2 rounded-lg bg-warning/15 p-2 text-xs text-warning"
            onClick={() => configure("title", title.key)}
          >
            {data.active_title === title.name ? "展示中：" : "展示稱號："}
            {title.name}
          </button>
        ))}
      </div>
      <div className="rounded-xl border border-border bg-card p-3">
        <h3 className="flex items-center gap-2 font-bold">
          <Save className="size-4" />
          配裝保存
        </h3>
        <p className="my-2 text-xs text-muted-foreground">
          儲存不會額外產生倍率。每次套用仍只生效一套，已開局的獎勵不變。
        </p>
        {Array.from({ length: data.preset_capacity }, (_, position) => {
          const preset = data.presets.find((p) => p.position === position)
          return (
            <div
              key={position}
              className="flex items-center justify-between gap-2 border-t border-border py-2 text-xs"
            >
              <span>{preset?.name ?? `配裝 ${position + 1}`}</span>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={disabled}
                  className="rounded bg-surface-2 p-2"
                  onClick={() =>
                    action.mutate(() =>
                      CollectionsService.savePreset({
                        position,
                        requestBody: {
                          name: `配裝 ${position + 1}`,
                          item_ids:
                            equipment?.items
                              .filter((i) => i.is_equipped)
                              .map((i) => i.id) ?? [],
                        },
                      }),
                    )
                  }
                >
                  保存目前配裝
                </button>
                {preset && (
                  <button
                    type="button"
                    disabled={disabled}
                    className="rounded bg-primary/15 p-2 text-primary"
                    onClick={() =>
                      action.mutate(() =>
                        CollectionsService.applyPreset({ position }),
                      )
                    }
                  >
                    套用
                  </button>
                )}
              </div>
            </div>
          )
        })}
        {data.preset_capacity < 5 && (
          <button
            type="button"
            disabled={disabled || userBlueprints < 10}
            className="mt-2 flex items-center gap-1 rounded bg-surface-2 p-2 text-xs disabled:opacity-40"
            onClick={() =>
              configure(
                "preset_slot",
                crypto.randomUUID(),
                data.preset_capacity,
              )
            }
          >
            <Sparkles className="size-3" />
            10 片圖紙增加配裝欄
            {userBlueprints < 10 ? `（還差 ${10 - userBlueprints} 片）` : ""}
          </button>
        )}
      </div>
    </section>
  )
}
