import { Link } from "@tanstack/react-router"
import {
  Award,
  CalendarDays,
  Coins,
  House,
  Mail,
  Menu,
  MessageCircle,
  ShoppingBag,
  Tv,
  UserRound,
} from "lucide-react"
import { type CSSProperties, useEffect, useState } from "react"
import { useClaimAccrual, useEconomyMe } from "@/hooks/useEconomy"
import { useHomeSummary } from "@/hooks/useHomeSummary"
import { BADGE_SLOTS, HOTSPOTS } from "./hotspots"
import {
  type HotspotId,
  mascotLine,
  menuItems,
  pickBubbles,
  roomImage,
} from "./logic"
import { MascotGuide } from "./MascotGuide"
import { RoomMenu } from "./RoomMenu"

const GUIDE_SEEN_KEY = "room-guide-seen"

// 房間圖（stage-0～6）的實際像素尺寸；七張一樣大
const ROOM_WIDTH = 941
const ROOM_HEIGHT = 1672
const ROOM_ASPECT = `${ROOM_WIDTH} / ${ROOM_HEIGHT}`

const HOTSPOT_LINKS = {
  phone: { to: "/scenarios", label: "情境對抗", icon: MessageCircle },
  tv: { to: "/quick/swipe", label: "滑卡訓練", icon: Tv },
  letters: { to: "/quick/quiz", label: "訊息判讀", icon: Mail },
  calendar: { to: "/daily", label: "每日訓練", icon: CalendarDays },
  bookshelf: { to: "/exam", label: "檢測", icon: Award },
} as const satisfies Record<
  HotspotId,
  {
    to: "/scenarios" | "/quick/swipe" | "/quick/quiz" | "/daily" | "/exam"
    label: string
    icon: typeof Tv
  }
>

function taipeiToday(): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Taipei",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date())
}

function guideSeenToday(): boolean {
  try {
    return localStorage.getItem(GUIDE_SEEN_KEY) === taipeiToday()
  } catch {
    return false
  }
}

function rememberGuide(): void {
  try {
    localStorage.setItem(GUIDE_SEEN_KEY, taipeiToday())
  } catch {
    /* 隱私模式寫不進去時，這次仍把對話框留著。 */
  }
}

function SceneImage({
  src,
  className,
  style,
}: {
  src: string
  className?: string
  style?: CSSProperties
}) {
  const [failed, setFailed] = useState(false)
  if (failed) {
    return <div className={`bg-surface-2 ${className ?? ""}`} style={style} />
  }
  return (
    <img
      src={src}
      alt=""
      className={className}
      style={style}
      onError={() => setFailed(true)}
    />
  )
}

export function RoomScene() {
  const summary = useHomeSummary()
  const economy = useEconomyMe()
  const { mutate: claim, isPending } = useClaimAccrual()
  const data = summary.data
  const bubbles = data ? pickBubbles(data) : []
  const line = data ? mascotLine(data) : null
  const items = data ? menuItems(data) : []
  const [menuOpen, setMenuOpen] = useState(false)
  const [guideOpen, setGuideOpen] = useState(() => !guideSeenToday())
  const cash = economy.data?.cash ?? 0
  const pending = economy.data?.pending_accrual ?? 0
  const streakDays = economy.data?.streak_days ?? 0
  const bubbleCount = bubbles.reduce(
    (sum, bubble) => sum + (bubble.count ?? 0),
    0,
  )

  useEffect(() => {
    if (data?.exam_active_attempt_id) setGuideOpen(true)
  }, [data?.exam_active_attempt_id])

  useEffect(() => {
    if (guideOpen) rememberGuide()
  }, [guideOpen])

  const room = roomImage(data?.room_stage ?? 0)
  return (
    // overflow-clip 而不是 overflow-hidden：hidden 仍可被程式捲動，點吉祥物時焦點會把整個房間捲歪
    <section
      data-testid="home-hero"
      className="relative mx-auto flex h-full w-full max-w-md items-end justify-center overflow-clip bg-surface-2"
      style={{ containerType: "size" }}
    >
      {/* 螢幕比房間圖細長時，上方空出來的地方鋪同一張圖的模糊版，不讓房間被裁切 */}
      <SceneImage
        src={room}
        className="absolute inset-0 size-full scale-110 object-cover blur-md"
      />
      {/* 圖框照房間圖的實際比例，熱區的百分比座標才會對準物件 */}
      <div
        data-testid="room-frame"
        className="relative"
        style={{
          aspectRatio: ROOM_ASPECT,
          width: `min(100cqw, calc(100cqh * ${ROOM_WIDTH} / ${ROOM_HEIGHT}))`,
        }}
      >
        <SceneImage src={room} className="absolute inset-0 size-full" />
        {(data?.badges ?? [])
          .slice(0, BADGE_SLOTS.length)
          .map((code, index) => {
            const slot = BADGE_SLOTS[index]
            if (!slot) return null
            return (
              <SceneImage
                key={code}
                src={`/assets/badge/${code}.webp`}
                className="absolute z-10 size-8 -translate-x-1/2 -translate-y-1/2 object-contain"
                style={{ left: `${slot.x}%`, top: `${slot.y}%` }}
              />
            )
          })}
        {(Object.keys(HOTSPOT_LINKS) as HotspotId[]).map((id) => {
          const spec = HOTSPOT_LINKS[id]
          const spot = HOTSPOTS[id]
          const bubble = bubbles.find((item) => item.id === id)
          const Icon = spec.icon
          return (
            <Link
              key={id}
              to={spec.to}
              data-testid={`hotspot-${id}`}
              aria-label={spec.label}
              style={{ left: `${spot.x}%`, top: `${spot.y}%` }}
              className="absolute z-10 flex size-16 -translate-x-1/2 -translate-y-1/2 items-center justify-center"
            >
              {bubble && (
                <span
                  data-testid={`bubble-${id}`}
                  className={`pointer-events-none absolute bottom-full mb-1 flex size-10 items-center justify-center rounded-full bg-card text-foreground shadow ${
                    bubble.highlight ? "ring-2 ring-warning" : ""
                  }`}
                >
                  <Icon aria-hidden className="size-5" />
                  {bubble.count != null && bubble.count > 0 && (
                    <span className="absolute -top-1 -right-1 flex min-w-4 items-center justify-center rounded-full bg-scam px-1 text-[10px] font-bold text-scam-foreground">
                      {bubble.count}
                    </span>
                  )}
                </span>
              )}
            </Link>
          )
        })}
        <button
          type="button"
          data-testid="hotspot-mascot"
          aria-label="吉祥物"
          style={{
            left: `${HOTSPOTS.mascot.x}%`,
            top: `${HOTSPOTS.mascot.y}%`,
          }}
          onClick={() => setGuideOpen(true)}
          className="absolute z-10 size-20 -translate-x-1/2 -translate-y-1/2"
        >
          <SceneImage
            src={data?.mascot_image_url ?? "/assets/mascot/shiba/base.webp"}
            className="size-full object-contain"
          />
        </button>
        {/* 放左下：右下是放手機的小桌，手機泡泡在那裡 */}
        <div className="absolute bottom-4 left-3 z-20 flex gap-2">
          <Link
            to="/shop"
            data-testid="room-shop"
            className="flex items-center gap-1 rounded-xl bg-card px-3 py-2 text-xs font-bold text-card-foreground shadow"
          >
            <ShoppingBag aria-hidden className="size-3.5" />
            購物
          </Link>
          <Link
            to="/assets"
            data-testid="room-house"
            className="flex items-center gap-1 rounded-xl bg-card px-3 py-2 text-xs font-bold text-card-foreground shadow"
          >
            <House aria-hidden className="size-3.5" />
            房子
          </Link>
        </div>
      </div>
      <Link
        to="/me"
        data-testid="room-me"
        className="absolute top-3 left-3 z-20 flex items-center gap-1 rounded-full bg-card px-2.5 py-1.5 text-xs font-bold text-card-foreground shadow"
      >
        <UserRound aria-hidden className="size-3.5" />我
      </Link>
      <div className="absolute top-3 right-3 z-20 flex items-center gap-1">
        <Link
          to="/assets"
          data-testid="hdr-cash"
          className={`flex items-center gap-1 rounded-full bg-card px-2.5 py-1.5 text-xs font-bold shadow ${
            cash < 0 ? "text-destructive" : "text-card-foreground"
          }`}
        >
          <Coins aria-hidden className="size-3.5" />
          {cash.toLocaleString()}
        </Link>
        {pending > 0 && (
          <button
            type="button"
            disabled={isPending}
            onClick={() => claim()}
            className="rounded-full bg-legit px-2.5 py-1.5 text-xs font-bold text-legit-foreground disabled:opacity-50"
          >
            可領 {pending.toLocaleString()}
          </button>
        )}
      </div>
      <button
        type="button"
        data-testid="room-menu"
        onClick={() => setMenuOpen((open) => !open)}
        className="absolute top-14 right-3 z-50 flex items-center gap-1 rounded-full bg-card px-2.5 py-1.5 text-xs font-bold text-card-foreground shadow"
      >
        <Menu aria-hidden className="size-3.5" />
        選單
        {bubbleCount > 0 && (
          <span className="flex min-w-4 items-center justify-center rounded-full bg-scam px-1 text-[10px] text-scam-foreground">
            {bubbleCount}
          </span>
        )}
      </button>
      {menuOpen && (
        <button
          type="button"
          aria-label="收起選單"
          className="absolute inset-0 z-30 bg-black/50"
          onClick={() => setMenuOpen(false)}
        />
      )}
      {menuOpen && (
        <RoomMenu items={items} onNavigate={() => setMenuOpen(false)} />
      )}
      {guideOpen && (
        <MascotGuide
          line={line}
          streakDays={streakDays}
          onClose={() => setGuideOpen(false)}
        />
      )}
      {summary.isError && !data && (
        <p className="absolute bottom-16 left-3 z-20 max-w-[60%] rounded-xl bg-card px-3 py-2 text-xs text-card-foreground">
          房間資料讀不到，請再試一次。
        </p>
      )}
    </section>
  )
}
