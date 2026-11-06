import type { HomeSummary } from "@/hooks/useHomeSummary"
import type { HotspotId } from "./logic"

/** 導覽每一步要亮的東西；null 是整個畫面變暗、只有吉祥物說話 */
export type TourTarget =
  | HotspotId
  | "mascot"
  | "cash"
  | "progression"
  | "shop"
  | "menu"
  | null

export type TourStep = {
  target: TourTarget
  title: string
  text: string
  action?: { label: string; to: "/exam" | "/pretest" }
}

/** 導覽亮的東西在畫面上的位置：家具用點擊範圍，其他用頁首與選單按鈕 */
export const TOUR_TEST_IDS: Record<Exclude<TourTarget, null>, string> = {
  phone: "hotspot-phone",
  tv: "hotspot-tv",
  letters: "hotspot-letters",
  calendar: "hotspot-calendar",
  bookshelf: "hotspot-bookshelf",
  mascot: "hotspot-mascot",
  cash: "hdr-cash",
  progression: "room-progression",
  shop: "room-shop-row",
  menu: "room-menu",
}

const ROOM_STEPS: TourStep[] = [
  {
    target: null,
    title: "這是你的房間",
    text: "我是你的練習夥伴。房間裡會發光的東西都可以點，點下去就開始練習。我帶你看一圈。",
  },
  {
    target: "tv",
    title: "電視：滑卡訓練",
    text: "一張一張訊息卡片，往左滑是詐騙、往右滑是正常。最快的練法，適合先熱身。",
  },
  {
    target: "letters",
    title: "信件架：訊息判讀",
    text: "讀一則訊息判斷真假，再找出對方用了哪些話術，學會遇到可疑訊息該去哪裡查證。",
  },
  {
    target: "phone",
    title: "手機：情境對抗",
    text: "和 AI 扮演的角色聊天，對方可能是詐騙，也可能是正常人。聊完由你判斷。",
  },
  {
    target: "calendar",
    title: "月曆：每日訓練",
    text: "每天一份大家都一樣的 10 題，還有排行榜，成績每兩週結算一次發獎。升到第 5 級就會開放。",
  },
  {
    target: "bookshelf",
    title: "書櫃：檢測與徽章",
    text: "練得差不多了就來這裡考一次，70 分過關可以拿到徽章，徽章會擺在書櫃上。",
  },
  {
    target: "cash",
    title: "錢和經驗值",
    text: "練習答對就會拿到錢和經驗值。經驗值累積起來會升級，等級越高能玩的越多。",
  },
  {
    target: "progression",
    title: "裝備：讓獎勵變多",
    text: "練習也會累積養成經驗和鍛造能量，拿來裝備、強化工具，之後每一輪的獎勵就會變多。點進去會有完整的玩法說明。",
  },
  {
    target: "shop",
    title: "購物和房子",
    text: "錢可以拿去買新的吉祥物和房子。有了房子，房間會變漂亮，每天還會有收入。",
  },
  {
    target: "menu",
    title: "選單",
    text: "所有功能也都列在選單裡。忘了哪件家具是做什麼的，打開選單就看得到。",
  },
]

/** 結尾依身分帶去下一步；從選單重看的人只是關掉 */
function lastStep(s: HomeSummary, replay: boolean): TourStep {
  if (replay) {
    return {
      target: null,
      title: "導覽結束",
      text: "想再看一次，打開選單按「重看導覽」就好。",
    }
  }
  if (s.trial) {
    return {
      target: null,
      title: "先做一次檢測",
      text: "先做一次綜合檢測，再填問卷。做完就可以自由玩，到時候會有新手任務帶你每種都玩一次。",
      action: { label: "開始檢測", to: "/exam" },
    }
  }
  return {
    target: null,
    title: "先做個小測驗",
    text: "先看看你最容易被哪一種詐騙騙到。做完會有新手任務帶你每種都玩一次。",
    action: { label: "開始", to: "/pretest" },
  }
}

export function tourSteps(s: HomeSummary, replay: boolean): TourStep[] {
  return [...ROOM_STEPS, lastStep(s, replay)]
}
