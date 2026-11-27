import { Link } from "@tanstack/react-router"
import { BookOpenCheck, Layers, PawPrint, Sparkles } from "lucide-react"
import type { EstatePublic, IndustryPublic, ManagerPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog"
import { parseBigIntSafe } from "@/utils/money"
import { formatDuration, formatYuan, perSecond } from "./format"

const DIALOG = "max-w-[calc(100%-2rem)] gap-3 p-4 sm:max-w-sm"

/** 一種產業的詳情：產量從哪裡翻倍、升級卡、練習再答對幾題 */
export function IndustryDetailDialog({
  industry,
  reputation,
  reputationPercent,
  cash,
  busy,
  onClose,
  onBuyCard,
}: {
  industry: IndustryPublic | null
  reputation: string
  reputationPercent: string
  cash: bigint
  busy: boolean
  onClose: () => void
  onBuyCard: () => void
}) {
  if (!industry) return null
  const cardPrice =
    industry.card_price === null ? null : parseBigIntSafe(industry.card_price)
  const practiceLeft =
    industry.next_practice_milestone === null
      ? null
      : industry.next_practice_milestone - industry.practice_correct
  const quantityLeft =
    industry.next_quantity_milestone === null
      ? null
      : industry.next_quantity_milestone - industry.owned
  const topic = industry.category === "general" ? undefined : industry.category
  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent data-testid="industry-detail" className={DIALOG}>
        <DialogTitle className="text-lg font-bold">{industry.name}</DialogTitle>
        <DialogDescription className="text-sm text-card-foreground">
          {industry.owned > 0
            ? `${industry.owned} 間，每秒 ${perSecond(industry.income_per_hour)} 元`
            : "還沒有這種房產"}
        </DialogDescription>

        <ul className="space-y-2 text-sm">
          <Line
            icon={<Layers aria-hidden className="size-4 text-primary" />}
            label="間數翻倍"
            value={`${2 ** industry.quantity_doublings} 倍`}
            hint={
              quantityLeft === null
                ? "全部翻完了"
                : `再買 ${quantityLeft} 間到 ${industry.next_quantity_milestone} 間，再翻一倍`
            }
          />
          <Line
            icon={<BookOpenCheck aria-hidden className="size-4 text-legit" />}
            label={`練習「${industry.category_label}」`}
            value={`${2 ** industry.practice_doublings} 倍`}
            hint={
              practiceLeft === null
                ? `已經答對 ${industry.practice_correct} 題，全部翻完了`
                : `已經答對 ${industry.practice_correct} 題，再答對 ${practiceLeft} 題再翻一倍`
            }
          />
          <Line
            icon={<Sparkles aria-hidden className="size-4 text-warning" />}
            label="升級卡"
            value={`${industry.card_level}／${industry.max_card_level} 張`}
            hint={`共 ${2 ** industry.card_doublings} 倍，搬家也不會不見`}
          />
          <Line
            icon={<Sparkles aria-hidden className="size-4 text-primary" />}
            label="信譽"
            value={`${reputationPercent}%`}
            hint={`${reputation} 點，所有房產都算`}
          />
        </ul>

        <div className="flex flex-col gap-2">
          {cardPrice !== null && (
            <Button
              disabled={busy || cash < cardPrice || industry.owned === 0}
              onClick={onBuyCard}
              data-testid="buy-card"
            >
              買一張升級卡（{formatYuan(cardPrice)} 元）
            </Button>
          )}
          <Button variant="outline" asChild>
            <Link to="/learn" search={topic ? { topic } : {}} onClick={onClose}>
              去練「{industry.category_label}」
            </Link>
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function Line({
  icon,
  label,
  value,
  hint,
}: {
  icon: React.ReactNode
  label: string
  value: string
  hint: string
}) {
  return (
    <li className="rounded-xl bg-surface-2 px-3 py-2">
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-1.5 font-semibold">
          {icon}
          {label}
        </span>
        <span className="font-bold tabular-nums">{value}</span>
      </div>
      <p className="mt-0.5 text-xs text-muted-foreground">{hint}</p>
    </li>
  )
}

/** 派吉祥物當經理：已經在別的房產當經理的會被調過來 */
export function ManagerDialog({
  industry,
  estate,
  busy,
  onClose,
  onPick,
}: {
  industry: IndustryPublic | null
  estate: EstatePublic
  busy: boolean
  onClose: () => void
  onPick: (itemId: string | null) => void
}) {
  if (!industry) return null
  const working = estate.industries
    .filter((i) => i.manager && i.tier_id !== industry.tier_id)
    .map((i) => ({ manager: i.manager as ManagerPublic, at: i.name }))
  const options: { manager: ManagerPublic; at?: string }[] = [
    ...estate.managers_available.map((manager) => ({ manager })),
    ...working,
  ]
  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent data-testid="manager-dialog" className={DIALOG}>
        <DialogTitle className="text-lg font-bold">
          {industry.name}的經理
        </DialogTitle>
        <DialogDescription className="text-sm text-card-foreground">
          有經理就會自動收租，沒開遊戲也照收，最多 {estate.offline_cap_hours}{" "}
          小時。
        </DialogDescription>
        <ul className="grid grid-cols-3 gap-2">
          {options.map(({ manager, at }) => (
            <li key={manager.item_id}>
              <button
                type="button"
                disabled={busy}
                onClick={() => onPick(manager.item_id)}
                className="flex w-full flex-col items-center gap-1 rounded-2xl border border-border bg-card p-2 hover:bg-surface-2"
              >
                <img
                  src={manager.image_url}
                  alt=""
                  className="size-14 object-contain"
                />
                <span className="text-sm font-bold">{manager.name}</span>
                <span className="text-[11px] text-muted-foreground">
                  {at ? `從${at}調來` : "有空"}
                </span>
              </button>
            </li>
          ))}
        </ul>
        {estate.managers_available.length === 0 && (
          <p className="text-xs text-muted-foreground">
            吉祥物都在別的房產當經理了。到商店買新的吉祥物，就能多派一個。
          </p>
        )}
        <div className="flex gap-2">
          <Button variant="outline" className="flex-1" asChild>
            <Link to="/shop" onClick={onClose}>
              <PawPrint aria-hidden className="size-4" />
              去商店
            </Link>
          </Button>
          {industry.manager && (
            <Button
              variant="outline"
              className="flex-1"
              disabled={busy}
              onClick={() => onPick(null)}
            >
              收回經理
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

/** 搬家確認：說清楚什麼會重來、什麼會留著 */
export function MoveDialog({
  estate,
  open,
  busy,
  onClose,
  onConfirm,
}: {
  estate: EstatePublic
  open: boolean
  busy: boolean
  onClose: () => void
  onConfirm: () => void
}) {
  const gain = parseBigIntSafe(estate.pending_reputation)
  const after =
    parseBigIntSafe(estate.reputation_percent) +
    gain * BigInt(estate.reputation_step_percent)
  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent data-testid="move-dialog" className={DIALOG}>
        <DialogTitle className="text-lg font-bold">確定要搬家嗎</DialogTitle>
        <DialogDescription className="text-sm leading-relaxed text-card-foreground">
          搬家後房產回到一間雅房，錢回到 1,000 元。換到 {formatYuan(gain)}{" "}
          點信譽，之後所有收入是原本的 {formatYuan(after)}%。
        </DialogDescription>
        <p className="rounded-xl bg-surface-2 px-3 py-2 text-sm">
          會留著的：升級卡、經理、練習的翻倍、榮譽。
        </p>
        <div className="flex gap-2">
          <Button variant="outline" className="flex-1" onClick={onClose}>
            再想想
          </Button>
          <Button
            className="flex-1"
            disabled={busy || gain <= 0n}
            onClick={onConfirm}
            data-testid="move-confirm"
          >
            搬家
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

/** 回來時：經理在你不在的時候收了多少 */
export function AwayDialog({
  away,
  onClose,
}: {
  away: EstatePublic["away"]
  onClose: () => void
}) {
  if (!away) return null
  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent data-testid="away-dialog" className={DIALOG}>
        <DialogTitle className="text-lg font-bold">歡迎回來</DialogTitle>
        <DialogDescription className="text-sm leading-relaxed text-card-foreground">
          你不在的 {formatDuration(away.seconds)}，經理幫你收了{" "}
          <strong className="text-legit">{formatYuan(away.earned)} 元</strong>
          ，已經放進錢包。
        </DialogDescription>
        {away.capped && (
          <p className="text-xs text-muted-foreground">
            經理最多幫你收 24 小時，常回來看看收得比較多。
          </p>
        )}
        <Button onClick={onClose}>收下</Button>
      </DialogContent>
    </Dialog>
  )
}

/** 舊制度換算成經營的說明，只出現一次 */
export function LegacyDialog({
  lines,
  busy,
  onClose,
}: {
  lines: string[]
  busy: boolean
  onClose: () => void
}) {
  if (lines.length === 0) return null
  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent data-testid="legacy-dialog" className={DIALOG}>
        <DialogTitle className="text-lg font-bold">養成改成經營了</DialogTitle>
        <DialogDescription className="text-sm text-card-foreground">
          原本的東西都換過來了，不會少：
        </DialogDescription>
        <ul className="list-disc space-y-1 pl-5 text-sm">
          {lines.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
        <Button disabled={busy} onClick={onClose}>
          知道了
        </Button>
      </DialogContent>
    </Dialog>
  )
}
