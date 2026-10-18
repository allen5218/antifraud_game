import { Link } from "@tanstack/react-router"
import { Fragment } from "react"
import { HOTSPOT_LINKS } from "./hotspotLinks"
import type { RoomBadge as Badge, HotspotId } from "./logic"
import { RoomBadge } from "./RoomBadge"
import {
  badgeRects,
  ROOM_WORLD,
  type RoomLayer,
  roomBackground,
  roomBoxes,
  roomLayers,
} from "./roomArt"
import { clampToView, type Rect, shiftIntoView, toScreen } from "./stage"
import { useStageLayout } from "./useStageLayout"

const MIN_TAP = 44 // 手指點得到的最小範圍（px）
const VIEW_INSET = 14 // 點擊範圍離畫面邊緣至少這麼遠，右上角的紅色標記才不會貼邊

type Props = {
  stage: number
  mascotSrc: string
  badges: Partial<Record<HotspotId, Badge>>
  paused: HotspotId[]
  strong: HotspotId | null
  examBadges: string[]
  onMascot: () => void
  onRoomShown: () => void
}

/** 擴大太小的點擊範圍，中心不變 */
function tapRect(rect: Rect): Rect {
  const w = Math.max(rect.w, MIN_TAP)
  const h = Math.max(rect.h, MIN_TAP)
  return { x: rect.x - (w - rect.w) / 2, y: rect.y - (h - rect.h) / 2, w, h }
}

/**
 * 畫面上的點擊範圍：先夾進可見範圍、撐到手指點得到的大小，再整塊移進畫面。
 * 物件被裁到一點時，點擊位置與右上角的紅色標記仍留在畫面裡。
 */
function tapBox(rect: Rect, viewW: number, viewH: number) {
  const visible = viewW > 0 ? clampToView(rect, viewW, viewH, VIEW_INSET) : rect
  const tap = tapRect(visible)
  const box = viewW > 0 ? shiftIntoView(tap, viewW, viewH, VIEW_INSET) : tap
  return { left: box.x, top: box.y, width: box.w, height: box.h }
}

/**
 * 房間舞台：整張房間圖與剪下來的家具圖層在固定大小的世界裡、整個一起縮放（stage.ts），
 * 點擊範圍與紅色標記放在舞台外的一層，用換算後的位置擺，紅點才不會跟著縮小。
 * 物件上不放圖示泡泡（使用者 10-18：「泡泡都拿掉」），要去哪裡靠呼吸光（推薦的那件比較快）、紅點與選單。
 */
export function RoomStage({
  stage,
  mascotSrc,
  badges,
  paused,
  strong,
  examBadges,
  onMascot,
  onRoomShown,
}: Props) {
  const { ref, layout, view } = useStageLayout(ROOM_WORLD)
  const layers = roomLayers(stage, mascotSrc)
  const glows = (layer: RoomLayer) =>
    layer.target === "mascot" || !paused.includes(layer.target)
  const shelfBadges = badgeRects(roomBoxes(stage), examBadges.length)

  return (
    <div ref={ref} data-testid="room-stage" className="absolute inset-0">
      <div
        aria-hidden="true"
        className="absolute top-0 left-0 origin-top-left select-none"
        style={
          {
            width: ROOM_WORLD.width,
            height: ROOM_WORLD.height,
            transform: `translate(${layout.x}px, ${layout.y}px) scale(${layout.scale})`,
            "--room-px": layout.scale > 0 ? `${1 / layout.scale}px` : "1px",
          } as React.CSSProperties
        }
      >
        <img
          data-testid="room-bg"
          src={roomBackground(stage)}
          alt=""
          draggable={false}
          onLoad={onRoomShown}
          onError={onRoomShown}
          className="absolute inset-0 size-full"
        />
        {layers.map((layer) => {
          const r = layer.box
          const box = { left: r.x, top: r.y, width: r.w, height: r.h }
          return (
            <Fragment key={layer.id}>
              {glows(layer) && (
                <img
                  src={layer.src}
                  alt=""
                  draggable={false}
                  data-testid={`glow-${layer.id}`}
                  data-strong={layer.target === strong}
                  className="room-glow absolute"
                  style={box}
                />
              )}
              <img
                data-testid={`layer-${layer.id}`}
                src={layer.src}
                alt=""
                draggable={false}
                className="absolute"
                style={box}
              />
              {layer.id === "bookshelf" &&
                shelfBadges.map((rect, index) => (
                  <img
                    key={examBadges[index]}
                    src={`/assets/badge/${examBadges[index]}.webp`}
                    alt=""
                    draggable={false}
                    className="absolute object-contain"
                    style={{
                      left: rect.x,
                      top: rect.y,
                      width: rect.w,
                      height: rect.h,
                    }}
                  />
                ))}
            </Fragment>
          )
        })}
      </div>
      {layers.map((layer) => {
        const screen = toScreen(layer.box, layout)
        if (layer.target === "mascot") {
          return (
            <button
              key={layer.id}
              type="button"
              data-testid="hotspot-mascot"
              aria-label="吉祥物"
              onClick={onMascot}
              className="absolute z-10 rounded-3xl transition-transform active:scale-95"
              style={tapBox(screen, view.width, view.height)}
            />
          )
        }
        const id = layer.target
        const spec = HOTSPOT_LINKS[id]
        const badge = badges[id]
        return (
          <Link
            key={layer.id}
            to={spec.to}
            data-testid={`hotspot-${id}`}
            aria-label={spec.label}
            className="absolute z-10 rounded-xl transition-transform active:scale-95"
            style={tapBox(screen, view.width, view.height)}
          >
            {badge && <RoomBadge badge={badge} testId={`badge-${id}`} />}
          </Link>
        )
      })}
    </div>
  )
}
