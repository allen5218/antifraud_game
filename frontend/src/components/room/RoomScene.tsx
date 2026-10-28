import { Link, useRouter } from "@tanstack/react-router"
import {
  Coins,
  GraduationCap,
  House,
  Menu,
  QrCode,
  ShoppingBag,
  UserRound,
} from "lucide-react"
import { useEffect, useState } from "react"
import { useClaimAccrual, useEconomyMe } from "@/hooks/useEconomy"
import { useHomeSummary } from "@/hooks/useHomeSummary"
import {
  mascotLine,
  mascotPose,
  menuItems,
  pausedHotspots,
  pickBubbles,
  poseImage,
  recommended,
  roomBadges,
  trialStep,
} from "./logic"
import { MascotGuide } from "./MascotGuide"
import { RoomMenu } from "./RoomMenu"
import { RoomStage } from "./RoomStage"

const GUIDE_SEEN_KEY = "room-guide-seen"
const LAST_ROOM_KEY = "room-last-look"
const DEFAULT_MASCOT = "/assets/mascot/shiba/base.webp"

// 房間裡每個入口的頁面：房間資料讀到後先載入它們的程式與資料，點下去就能直接換頁
const PRELOAD_ROUTES = [
  "/me",
  "/shop",
  "/assets",
  "/scenarios",
  "/quick/swipe",
  "/quick/quiz",
  "/daily",
  "/exam",
] as const

// 手指按下時縮一下，網路慢的時候也看得出有按到
const PRESS = "transition-transform active:scale-95"

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

type RoomLook = { stage: number; mascot: string }

/**
 * 上次看到的房間階段與吉祥物。打開網站時圖片可能已在快取、資料還在路上，
 * 先用上次的樣子，免得有房子、換過吉祥物的玩家先閃一下破舊房間和柴犬。
 */
function readLastLook(): RoomLook | null {
  try {
    const raw = localStorage.getItem(LAST_ROOM_KEY)
    if (!raw) return null
    const look = JSON.parse(raw) as Partial<RoomLook>
    if (typeof look.stage !== "number" || typeof look.mascot !== "string") {
      return null
    }
    return { stage: look.stage, mascot: look.mascot }
  } catch {
    return null
  }
}

function rememberLook(look: RoomLook): void {
  try {
    localStorage.setItem(LAST_ROOM_KEY, JSON.stringify(look))
  } catch {
    /* 寫不進去就下次照預設顯示 */
  }
}

export function RoomScene() {
  const router = useRouter()
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

  // 試測還有下一步（檢測或問卷）時，每次回房間都打開對話框帶路
  const step = data ? trialStep(data) : null
  useEffect(() => {
    if (step) setGuideOpen(true)
  }, [step])

  useEffect(() => {
    if (guideOpen) rememberGuide()
  }, [guideOpen])

  // 房間圖出現之後才預先載入各入口，免得跟房間圖搶網路
  const [roomShown, setRoomShown] = useState(false)
  useEffect(() => {
    if (!roomShown) return
    const timer = setTimeout(() => {
      for (const to of PRELOAD_ROUTES)
        router.preloadRoute({ to }).catch(() => {})
    }, 300)
    return () => clearTimeout(timer)
  }, [roomShown, router])

  const [lastLook] = useState(readLastLook)
  const stage = data?.room_stage
  const mascotSrc = data?.mascot_image_url
  useEffect(() => {
    if (stage != null && mascotSrc) rememberLook({ stage, mascot: mascotSrc })
  }, [stage, mascotSrc])
  const pose = data ? mascotPose(data, guideOpen) : "base"
  const mascotShown = poseImage(
    mascotSrc ?? lastLook?.mascot ?? DEFAULT_MASCOT,
    pose,
  )

  return (
    // overflow-clip 而不是 overflow-hidden：hidden 仍可被程式捲動，點吉祥物時焦點會把整個房間捲歪
    <section
      data-testid="home-hero"
      className="relative h-full w-full overflow-clip bg-surface-2"
    >
      <RoomStage
        stage={stage ?? lastLook?.stage ?? 0}
        mascotSrc={mascotShown}
        badges={data ? roomBadges(data) : {}}
        paused={data ? pausedHotspots(data) : []}
        strong={data ? recommended(data) : null}
        examBadges={data?.badges ?? []}
        onMascot={() => setGuideOpen(true)}
        onRoomShown={() => setRoomShown(true)}
      />
      {/* 購物與房子貼著畫面左下，避開手機的 Home 橫條 */}
      <div className="absolute bottom-[calc(env(safe-area-inset-bottom)+1rem)] left-3 z-20 flex gap-2">
        <Link
          to="/shop"
          data-testid="room-shop"
          className={`flex items-center gap-1 rounded-xl bg-card px-3 py-2 text-xs font-bold text-card-foreground shadow ${PRESS}`}
        >
          <ShoppingBag aria-hidden className="size-3.5" />
          購物
        </Link>
        <Link
          to="/assets"
          data-testid="room-house"
          className={`flex items-center gap-1 rounded-xl bg-card px-3 py-2 text-xs font-bold text-card-foreground shadow ${PRESS}`}
        >
          <House aria-hidden className="size-3.5" />
          房子
        </Link>
      </div>
      <div className="absolute top-[calc(env(safe-area-inset-top)+0.75rem)] left-3 z-20 flex items-center gap-1">
        <Link
          to="/me"
          data-testid="room-me"
          className={`flex items-center gap-1 rounded-full bg-card px-2.5 py-1.5 text-xs font-bold text-card-foreground shadow ${PRESS}`}
        >
          <UserRound aria-hidden className="size-3.5" />我
        </Link>
        {data?.admin_access && (
          <Link
            to="/admin/cohorts"
            data-testid="room-admin"
            className={`flex items-center gap-1 rounded-full bg-primary px-2.5 py-1.5 text-xs font-bold text-primary-foreground shadow ${PRESS}`}
          >
            <QrCode aria-hidden className="size-3.5" />
            試測管理
          </Link>
        )}
        {(data?.teacher_status === "approved" || data?.admin_access) && (
          <Link
            to="/classes"
            data-testid="room-classes"
            className={`flex items-center gap-1 rounded-full bg-primary px-2.5 py-1.5 text-xs font-bold text-primary-foreground shadow ${PRESS}`}
          >
            <GraduationCap aria-hidden className="size-3.5" />
            班級管理
          </Link>
        )}
      </div>
      <div className="absolute top-[calc(env(safe-area-inset-top)+0.75rem)] right-3 z-20 flex items-center gap-1">
        <Link
          to="/assets"
          data-testid="hdr-cash"
          className={`flex items-center gap-1 rounded-full bg-card px-2.5 py-1.5 text-xs font-bold shadow ${PRESS} ${
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
        className={`absolute top-[calc(env(safe-area-inset-top)+3.5rem)] right-3 z-50 flex items-center gap-1 rounded-full bg-card px-2.5 py-1.5 text-xs font-bold text-card-foreground shadow ${PRESS}`}
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
