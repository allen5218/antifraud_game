import { useId, useState } from "react"
import { cn } from "@/lib/utils"
import {
  ART_H,
  ART_W,
  type CardArtInput,
  layoutCardArt,
  parseCardArt,
} from "./cardArtLayout"
import { castHref, propHref, sceneHref } from "./cardArtManifest"

// 插圖本身用固定暖色（跟房間圖一樣，不跟深色模式換色），這兩色屬於插圖的一部分
const BUBBLE = "#FFFDF8"
const VIDEO_BG = "#DCE8E6"

export interface CardArtProps extends CardArtInput {
  /** 給螢幕閱讀器的圖片說明；不給就當裝飾圖 */
  label?: string
  className?: string
}

/**
 * 日常卡片的插圖：場景墊底，角色站在地上、道具放在右邊。
 * 題庫的 art 欄位直接傳進來；清單外的 id 略過，圖片載入失敗的那一層藏起來。
 */
export function CardArt({ label, className, ...input }: CardArtProps) {
  const spec = parseCardArt(input)
  const layout = layoutCardArt(spec)
  const uid = useId().replace(/[^\w-]/g, "")
  const [failed, setFailed] = useState<ReadonlySet<string>>(() => new Set())
  const ok = (href: string) => !failed.has(href)
  const onError = (href: string) => () =>
    setFailed((prev) => new Set(prev).add(href))

  const scene = spec.scene ? sceneHref(spec.scene) : null

  return (
    <svg
      viewBox={`0 0 ${ART_W} ${ART_H}`}
      className={cn("block h-auto w-full", className)}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    >
      <rect
        data-layer="backdrop"
        width={ART_W}
        height={ART_H}
        className="fill-surface-2"
      />
      {scene && ok(scene) && (
        <image
          data-layer="scene"
          href={scene}
          width={ART_W}
          height={ART_H}
          onError={onError(scene)}
        />
      )}
      {layout.cast.map((slot, i) => {
        const href = castHref(slot.id, slot.pose)
        const image = ok(href) && (
          <image
            data-layer="cast"
            href={href}
            x={slot.x}
            y={slot.y}
            width={slot.w}
            height={slot.h}
            transform={
              slot.mirror
                ? `translate(${slot.x * 2 + slot.w} 0) scale(-1 1)`
                : undefined
            }
            onError={onError(href)}
          />
        )
        if (!slot.clip) return <g key={`${slot.id}-${i}`}>{image}</g>
        const clipId = `${uid}-clip-${i}`
        const { x, y, w, h } = slot.clip
        return (
          <g key={`${slot.id}-${i}`}>
            <clipPath id={clipId}>
              <rect x={x} y={y} width={w} height={h} rx={i === 0 ? 0 : 8} />
            </clipPath>
            <g clipPath={`url(#${clipId})`}>
              <rect x={x} y={y} width={w} height={h} fill={VIDEO_BG} />
              {image}
            </g>
            {i > 0 && (
              <rect
                x={x}
                y={y}
                width={w}
                height={h}
                rx={8}
                fill="none"
                stroke={BUBBLE}
                strokeWidth={2.5}
              />
            )}
          </g>
        )
      })}
      {layout.props.map((slot) => {
        const href = propHref(slot.id)
        if (!ok(href)) return null
        return (
          <g key={slot.id}>
            {slot.bubble && (
              <circle
                cx={slot.x + slot.size / 2}
                cy={slot.y + slot.size / 2}
                r={slot.size * 0.52}
                fill={BUBBLE}
                opacity={0.92}
              />
            )}
            <image
              data-layer="prop"
              href={href}
              x={slot.x}
              y={slot.y}
              width={slot.size}
              height={slot.size}
              onError={onError(href)}
            />
          </g>
        )
      })}
    </svg>
  )
}
