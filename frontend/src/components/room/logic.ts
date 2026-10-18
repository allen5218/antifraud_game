import type { HomeSummary } from "@/hooks/useHomeSummary"
import { fraudTypeLabel } from "@/lib/fraudTypes"

export type HotspotId = "phone" | "tv" | "letters" | "calendar" | "bookshelf"

export type Bubble = {
  id: HotspotId
  count?: number
  highlight: boolean
}

export type MascotLine = {
  text: string
  highlight: HotspotId | null
  action?: { label: string; to: string }
}

export type MenuTo =
  | "/scenarios"
  | "/quick/swipe"
  | "/quick/quiz"
  | "/daily"
  | "/leaderboard"
  | "/exam"

export type MenuItem = {
  id: HotspotId | "leaderboard" | "badges"
  label: string
  status: string
  done: boolean
  to: MenuTo
}

export type MascotPose = "base" | "point" | "cheer" | "think"

/**
 * 吉祥物的姿勢跟著玩家的狀態：卡在檢測或補考時在想、練夠或今天做完時歡呼、
 * 要帶玩家去做事（沒做前測、正在說話）時指著，其他時候招手。
 */
export function mascotPose(s: HomeSummary, talking: boolean): MascotPose {
  if (s.exam_active_attempt_id) return "think"
  if (s.retake && !s.retake.gate.met) return "think"
  if (s.retake?.gate.met) return "cheer"
  if (!s.pretest_done || talking) return "point"
  if (s.daily_unlocked && s.daily_done) return "cheer"
  return "base"
}

/** 後端只回招手那張（.../base.webp），其他姿勢在同一個資料夾。 */
export function poseImage(baseUrl: string, pose: MascotPose): string {
  return baseUrl.replace(/\/base\.webp$/, `/${pose}.webp`)
}

function remain(done: number, need: number): number {
  return Math.max(0, need - done)
}

function retakeGaps(s: HomeSummary): { id: HotspotId; count: number }[] {
  const gate = s.retake?.gate
  if (!gate) return []
  const gaps: { id: HotspotId; count: number }[] = []
  const swipe = remain(gate.swipe.done, gate.swipe.need)
  const quiz = remain(gate.quiz.done, gate.quiz.need)
  const scenario = remain(gate.scenario.done, gate.scenario.need)
  if (swipe > 0) gaps.push({ id: "tv", count: swipe })
  if (quiz > 0) gaps.push({ id: "letters", count: quiz })
  if (scenario > 0) gaps.push({ id: "phone", count: scenario })
  return gaps
}

/** 泡泡第一步：吉祥物要玩家先去的物件。沒做前測時對話框不指物件，泡泡仍先亮電視。 */
export function recommended(s: HomeSummary): HotspotId | null {
  if (s.exam_active_attempt_id) return "bookshelf"
  if (s.retake && !s.retake.gate.met) return retakeGaps(s)[0]?.id ?? null
  if (s.retake?.gate.met) return "bookshelf"
  return "tv"
}

export function pickBubbles(s: HomeSummary): Bubble[] {
  const bubbles: Bubble[] = []
  const add = (
    id: HotspotId,
    extra: { count?: number; highlight?: boolean },
  ) => {
    const found = bubbles.find((bubble) => bubble.id === id)
    if (found) {
      if (extra.count !== undefined && found.count === undefined) {
        found.count = extra.count
      }
      if (extra.highlight) found.highlight = true
      return
    }
    if (bubbles.length >= 3) return
    const bubble: Bubble = { id, highlight: Boolean(extra.highlight) }
    if (extra.count !== undefined) bubble.count = extra.count
    bubbles.push(bubble)
  }

  const highlight = recommended(s)
  if (highlight) add(highlight, { highlight: true })
  // 檢測中三種訓練與每日訓練都暫停，不要再招呼玩家去點
  if (s.exam_active_attempt_id) return bubbles
  if (s.retake && !s.retake.gate.met) {
    for (const gap of retakeGaps(s)) add(gap.id, { count: gap.count })
  }
  if (s.inbox_pending > 0) add("phone", { count: s.inbox_pending })
  if (s.daily_unlocked && !s.daily_done) add("calendar", {})
  if (s.exam_can_start) add("bookshelf", {})
  return bubbles
}

/** 物件上的紅色標記：有確切數量就顯示數字（像手機 App 的未讀數），只是「有新的」就顯示圓點。 */
export type RoomBadge = { count: number } | { dot: true }

export function roomBadges(
  s: HomeSummary,
): Partial<Record<HotspotId, RoomBadge>> {
  const badges: Partial<Record<HotspotId, RoomBadge>> = {}
  if (s.exam_active_attempt_id) {
    badges.bookshelf = { dot: true }
    return badges
  }
  for (const gap of retakeGaps(s)) badges[gap.id] = { count: gap.count }
  if (s.inbox_pending > 0 && !badges.phone) {
    badges.phone = { count: s.inbox_pending }
  }
  if (s.daily_unlocked && !s.daily_done) badges.calendar = { dot: true }
  if (s.exam_can_start) badges.bookshelf = { dot: true }
  return badges
}

/** 檢測中三種訓練與每日訓練暫停，這些物件不再閃爍招呼玩家 */
export function pausedHotspots(s: HomeSummary): HotspotId[] {
  return s.exam_active_attempt_id ? ["phone", "tv", "letters", "calendar"] : []
}

export function mascotLine(s: HomeSummary): MascotLine {
  if (!s.pretest_done) {
    return {
      text: "歡迎！先做個小測驗，看看你最容易被哪一種詐騙騙到。",
      highlight: null,
      action: { label: "開始", to: "/pretest" },
    }
  }
  if (s.exam_active_attempt_id) {
    return { text: "檢測做完前，練習先暫停。", highlight: "bookshelf" }
  }
  if (s.retake && !s.retake.gate.met) {
    const gate = s.retake.gate
    const swipe = remain(gate.swipe.done, gate.swipe.need)
    const quiz = remain(gate.quiz.done, gate.quiz.need)
    const scenario = remain(gate.scenario.done, gate.scenario.need)
    const parts = [
      swipe > 0 ? `滑卡 ${swipe} 張` : "",
      quiz > 0 ? `訊息判讀 ${quiz} 題` : "",
      scenario > 0 ? `情境 ${scenario} 場` : "",
    ].filter((part) => part.length > 0)
    let text = `檢測沒過：先加強${fraudTypeLabel(s.retake.fraud_type)}。`
    if (parts.length > 0) text += `還差${parts.join("、")}。`
    if (
      swipe === 0 &&
      quiz === 0 &&
      scenario === 0 &&
      gate.recent.correct < gate.recent.need
    ) {
      text += `最近十題還要答對 ${gate.recent.need} 題，目前 ${gate.recent.correct} 題。`
    }
    return { text, highlight: retakeGaps(s)[0]?.id ?? null }
  }
  if (s.retake?.gate.met) {
    return { text: "可以再檢測了！", highlight: "bookshelf" }
  }
  if (s.focus_label) {
    return {
      text: `本輪加強：${s.focus_label}。先去練練看，做完就有錢。`,
      highlight: "tv",
    }
  }
  return { text: "先去練練看，做完就有錢。", highlight: "tv" }
}

const PAUSED = "檢測中暫停"

export function menuItems(s: HomeSummary): MenuItem[] {
  const gate = s.retake?.gate
  const swipeLeft = gate ? remain(gate.swipe.done, gate.swipe.need) : 0
  const quizLeft = gate ? remain(gate.quiz.done, gate.quiz.need) : 0
  const items: MenuItem[] = [
    {
      id: "phone",
      label: "情境對抗",
      status:
        s.inbox_pending > 0 ? `還有 ${s.inbox_pending} 人沒聊` : "都聊完了",
      done: s.inbox_pending === 0,
      to: "/scenarios",
    },
    {
      id: "tv",
      label: "滑卡訓練",
      status: swipeLeft > 0 ? `還差 ${swipeLeft} 張` : "可以練",
      done: false,
      to: "/quick/swipe",
    },
    {
      id: "letters",
      label: "訊息判讀",
      status: quizLeft > 0 ? `還差 ${quizLeft} 題` : "可以練",
      done: false,
      to: "/quick/quiz",
    },
    {
      id: "calendar",
      label: "每日訓練",
      status: !s.daily_unlocked
        ? "等級五才解鎖"
        : s.daily_done
          ? "今天做完了"
          : "今天還沒做",
      done: s.daily_done,
      to: "/daily",
    },
    {
      id: "bookshelf",
      label: "檢測",
      status: s.exam_active_attempt_id
        ? "還沒做完"
        : s.retake && !s.retake.gate.met
          ? "先補考"
          : s.exam_can_start
            ? "可以考"
            : "今天先休息",
      done: !s.exam_active_attempt_id && !s.exam_can_start,
      to: "/exam",
    },
    {
      id: "leaderboard",
      label: "排行榜",
      status: s.daily_unlocked ? "看今天和本週" : "等級五才解鎖",
      done: false,
      to: "/leaderboard",
    },
    {
      id: "badges",
      label: "我的徽章",
      status: s.badges.length > 0 ? `已有 ${s.badges.length} 個` : "還沒有",
      done: false,
      to: "/exam",
    },
  ]
  if (!s.exam_active_attempt_id) return items
  const training = new Set<MenuItem["id"]>([
    "phone",
    "tv",
    "letters",
    "calendar",
  ])
  return items.map((item) =>
    training.has(item.id) ? { ...item, status: PAUSED, done: true } : item,
  )
}
