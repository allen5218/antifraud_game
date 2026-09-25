import { UserRound } from "lucide-react"
import { FRAUD_TYPES } from "@/lib/fraudTypes"

/**
 * 情境聯絡人的頭貼。後端給的是 `<類型>-<1..3>` 這種代號,圖在 public/assets/avatar/。
 *
 * 同一類的詐騙者與正常角色共用同一組三張(後端 AVATAR_POOL),看頭貼猜不出身分。
 * 畫的是物件與風景而不是人像:名字與頭貼是分開抽的,人像會出現名字與長相對不上。
 * 認不得的值(改版前存的 emoji)顯示通用圖示,不直接把字串印出來。
 */
const AVATAR_KEY = new RegExp(`^(${FRAUD_TYPES.join("|")})-[1-3]$`)

export function ScenarioAvatar({
  avatar,
  className = "size-10",
}: {
  avatar: string
  className?: string
}) {
  if (AVATAR_KEY.test(avatar)) {
    return (
      <img
        src={`/assets/avatar/${avatar}.webp`}
        alt=""
        aria-hidden="true"
        loading="lazy"
        className={`shrink-0 rounded-full object-cover ${className}`}
      />
    )
  }
  return (
    <span
      aria-hidden="true"
      className={`flex shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground ${className}`}
    >
      <UserRound className="size-1/2" />
    </span>
  )
}
