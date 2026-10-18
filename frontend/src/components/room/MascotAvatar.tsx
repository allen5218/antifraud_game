import { useState } from "react"
import { useHomeSummary } from "@/hooks/useHomeSummary"

/**
 * 玩家正在展示的吉祥物。讀房間首頁同一份資料，商店換吉祥物時那份資料會重讀，這裡跟著換。
 * 還沒讀到或圖壞掉時只放底色塊，不先閃一下柴犬。
 */
export function MascotAvatar({ className }: { className?: string }) {
  const { data } = useHomeSummary()
  const src = data?.mascot_image_url
  const [brokenSrc, setBrokenSrc] = useState<string | null>(null)
  if (!src || brokenSrc === src) {
    return <div aria-hidden="true" className={`bg-surface-2 ${className}`} />
  }
  return (
    <img
      src={src}
      alt=""
      aria-hidden="true"
      width={64}
      height={64}
      onError={() => setBrokenSrc(src)}
      className={`bg-surface-2 object-cover ${className}`}
    />
  )
}
