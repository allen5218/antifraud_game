import { describe, expect, it, test } from "bun:test"
import type { HomeSummary } from "@/hooks/useHomeSummary"
import {
  mascotLine,
  mascotPose,
  menuItems,
  pausedHotspots,
  pickBubbles,
  poseImage,
  roomBadges,
} from "./logic"

function summary(overrides: Partial<HomeSummary> = {}): HomeSummary {
  return {
    room_stage: 0,
    mascot_image_url: "/assets/mascot/shiba/base.webp",
    pretest_done: true,
    inbox_pending: 0,
    daily_unlocked: false,
    daily_done: false,
    exam_active_attempt_id: null,
    exam_can_start: false,
    retake: null,
    focus_type: null,
    focus_label: null,
    badges: [],
    ...overrides,
  }
}

function retake(
  swipe: [number, number],
  quiz: [number, number],
  scenario: [number, number],
  recent: { correct: number; need: number } = { correct: 7, need: 7 },
  met = false,
) {
  return {
    fraud_type: "investment",
    gate: {
      fraud_type: "investment",
      swipe: { done: swipe[0], need: swipe[1] },
      quiz: { done: quiz[0], need: quiz[1] },
      scenario: { done: scenario[0], need: scenario[1] },
      recent: { correct: recent.correct, total: 10, need: recent.need },
      met,
    },
  }
}

describe("pickBubbles", () => {
  it("新玩家先亮電視，再顯示沒收完的手機", () => {
    expect(
      pickBubbles(
        summary({
          pretest_done: false,
          inbox_pending: 5,
        }),
      ),
    ).toEqual([
      { id: "tv", highlight: true },
      { id: "phone", count: 5, highlight: false },
    ])
  })

  it("全部條件成立時只回 3 個且順序正確", () => {
    expect(
      pickBubbles(
        summary({
          inbox_pending: 4,
          daily_unlocked: true,
          daily_done: false,
          exam_can_start: true,
          focus_label: "投資詐騙",
          retake: retake([1, 6], [2, 5], [0, 1], { correct: 3, need: 7 }),
        }),
      ),
    ).toEqual([
      { id: "tv", count: 5, highlight: true },
      { id: "letters", count: 3, highlight: false },
      { id: "phone", count: 1, highlight: false },
    ])
  })

  it("同物件不重複", () => {
    expect(
      pickBubbles(
        summary({
          inbox_pending: 2,
          daily_unlocked: true,
          daily_done: false,
          exam_can_start: true,
          retake: retake([6, 6], [5, 5], [1, 1], { correct: 7, need: 7 }, true),
        }),
      ),
    ).toEqual([
      { id: "bookshelf", highlight: true },
      { id: "phone", count: 2, highlight: false },
      { id: "calendar", highlight: false },
    ])
  })
})

describe("pickBubbles 檢測中", () => {
  it("只亮書櫃，練習的泡泡都收起來", () => {
    expect(
      pickBubbles(
        summary({
          exam_active_attempt_id: "attempt-1",
          inbox_pending: 5,
          daily_unlocked: true,
          daily_done: false,
        }),
      ),
    ).toEqual([{ id: "bookshelf", highlight: true }])
  })
})

describe("mascotLine", () => {
  it("new player sees pretest prompt", () => {
    expect(mascotLine(summary({ pretest_done: false }))).toEqual({
      text: "歡迎！先做個小測驗，看看你最容易被哪一種詐騙騙到。",
      highlight: null,
      action: { label: "開始", to: "/pretest" },
    })
  })

  it("mascotLine active exam", () => {
    expect(
      mascotLine(
        summary({
          exam_active_attempt_id: "attempt-1",
          retake: retake([0, 6], [0, 5], [0, 1]),
        }),
      ),
    ).toEqual({
      // 下面的卡片已經寫「你有一份檢測還沒做完」，這句不重複，改講練習為什麼點不進去
      text: "檢測做完前，練習先暫停。",
      highlight: "bookshelf",
    })
  })

  it("補考還沒練夠，零的那段不寫", () => {
    expect(
      mascotLine(
        summary({
          retake: retake([4, 6], [5, 5], [0, 1]),
        }),
      ),
    ).toEqual({
      text: "檢測沒過：先加強投資詐騙。還差滑卡 2 張、情境 1 場。",
      highlight: "tv",
    })
  })

  it("三項都夠但最近十題不夠，補上還要答對幾題", () => {
    expect(
      mascotLine(
        summary({
          retake: retake([6, 6], [5, 5], [1, 1], { correct: 4, need: 7 }),
        }),
      ),
    ).toEqual({
      text: "檢測沒過：先加強投資詐騙。最近十題還要答對 7 題，目前 4 題。",
      highlight: null,
    })
  })

  it("補考練夠可以再檢測", () => {
    expect(
      mascotLine(
        summary({
          retake: retake([6, 6], [5, 5], [1, 1], { correct: 7, need: 7 }, true),
        }),
      ),
    ).toEqual({
      text: "可以再檢測了！",
      highlight: "bookshelf",
    })
  })

  it("平常有練習重點就先帶去滑卡", () => {
    expect(mascotLine(summary({ focus_label: "假交友" }))).toEqual({
      text: "本輪加強：假交友。先去練練看，做完就有錢。",
      highlight: "tv",
    })
  })

  it("沒有練習重點只催去練", () => {
    expect(mascotLine(summary())).toEqual({
      text: "先去練練看，做完就有錢。",
      highlight: "tv",
    })
  })
})

describe("menuItems", () => {
  it("五個物件再加上排行榜和我的徽章", () => {
    const items = menuItems(
      summary({
        inbox_pending: 2,
        daily_unlocked: true,
        daily_done: true,
        exam_can_start: true,
      }),
    )
    expect(items.map((item) => item.id)).toEqual([
      "phone",
      "tv",
      "letters",
      "calendar",
      "bookshelf",
      "leaderboard",
      "badges",
    ])
    expect(items.map((item) => item.label)).toEqual([
      "情境對抗",
      "滑卡訓練",
      "訊息判讀",
      "每日訓練",
      "檢測",
      "排行榜",
      "我的徽章",
    ])
    expect(items.find((item) => item.id === "calendar")?.done).toBe(true)
    expect(items.find((item) => item.id === "phone")?.to).toBe("/scenarios")
  })
})

describe("menuItems 檢測中", () => {
  it("四種練習都寫暫停並變淡，檢測寫還沒做完", () => {
    const items = menuItems(
      summary({
        exam_active_attempt_id: "attempt-1",
        inbox_pending: 5,
        daily_unlocked: true,
        daily_done: false,
      }),
    )
    for (const id of ["phone", "tv", "letters", "calendar"] as const) {
      const item = items.find((entry) => entry.id === id)
      expect(item?.status).toBe("檢測中暫停")
      expect(item?.done).toBe(true)
    }
    const exam = items.find((entry) => entry.id === "bookshelf")
    expect(exam?.status).toBe("還沒做完")
    expect(exam?.done).toBe(false)
  })
})

describe("mascotPose", () => {
  test("平常招手，說話時指著", () => {
    expect(mascotPose(summary(), false)).toBe("base")
    expect(mascotPose(summary(), true)).toBe("point")
  })

  test("還沒做前測指著開始", () => {
    expect(mascotPose(summary({ pretest_done: false }), false)).toBe("point")
  })

  test("檢測中、補考還沒練夠在想", () => {
    expect(mascotPose(summary({ exam_active_attempt_id: "a1" }), true)).toBe(
      "think",
    )
    expect(
      mascotPose(summary({ retake: retake([0, 6], [0, 5], [0, 1]) }), false),
    ).toBe("think")
  })

  test("補考練夠、今天的每日訓練做完歡呼", () => {
    expect(
      mascotPose(
        summary({ retake: retake([6, 6], [5, 5], [1, 1], undefined, true) }),
        false,
      ),
    ).toBe("cheer")
    expect(
      mascotPose(summary({ daily_unlocked: true, daily_done: true }), false),
    ).toBe("cheer")
  })
})

describe("poseImage", () => {
  test("把招手圖換成同一隻的其他姿勢", () => {
    expect(poseImage("/assets/mascot/fox/base.webp", "cheer")).toBe(
      "/assets/mascot/fox/cheer.webp",
    )
    expect(poseImage("/assets/mascot/red_panda/base.webp", "base")).toBe(
      "/assets/mascot/red_panda/base.webp",
    )
  })
})

describe("roomBadges", () => {
  test("情境收件匣顯示未讀數，每日訓練沒做顯示圓點", () => {
    expect(
      roomBadges(
        summary({ inbox_pending: 3, daily_unlocked: true, daily_done: false }),
      ),
    ).toEqual({ phone: { count: 3 }, calendar: { dot: true } })
  })

  test("補考期顯示各項還差多少", () => {
    expect(
      roomBadges(summary({ retake: retake([1, 6], [5, 5], [0, 1]) })),
    ).toEqual({ tv: { count: 5 }, phone: { count: 1 } })
  })

  test("檢測中只標書櫃，訓練物件暫停", () => {
    const s = summary({ exam_active_attempt_id: "a1", inbox_pending: 2 })
    expect(roomBadges(s)).toEqual({ bookshelf: { dot: true } })
    expect(pausedHotspots(s)).toEqual(["phone", "tv", "letters", "calendar"])
  })
})

describe("團隊題庫入口", () => {
  it("只有團隊成員或管理員的選單才有", () => {
    expect(menuItems(summary()).some((i) => i.id === "team")).toBe(false)
    const team = menuItems(summary({ team_access: true })).find(
      (i) => i.id === "team",
    )
    expect(team?.to).toBe("/team")
  })

  it("檢測中也不會變成暫停", () => {
    const team = menuItems(
      summary({ team_access: true, exam_active_attempt_id: "a" }),
    ).find((i) => i.id === "team")
    expect(team?.done).toBe(false)
    expect(team?.status).toBe("全部題目與答案")
  })
})

describe("試測問卷入口", () => {
  it("一般帳號和交過問卷的人沒有", () => {
    expect(menuItems(summary()).some((i) => i.id === "survey")).toBe(false)
  })

  it("檢測還沒做完時變淡並寫做完檢測後填", () => {
    const item = menuItems(summary({ survey_pending: true }))[0]
    expect(item).toMatchObject({
      id: "survey",
      to: "/survey",
      status: "做完檢測後填",
      done: true,
    })
  })

  it("做完檢測就可以填，放在選單最前面", () => {
    const item = menuItems(
      summary({ survey_pending: true, survey_ready: true }),
    )[0]
    expect(item).toMatchObject({ id: "survey", status: "還沒填", done: false })
  })
})

describe("試測管理入口", () => {
  it("只有管理員的選單才有，檢測中也不暫停", () => {
    expect(menuItems(summary()).some((i) => i.id === "admin")).toBe(false)
    const admin = menuItems(
      summary({ admin_access: true, exam_active_attempt_id: "a" }),
    ).find((i) => i.id === "admin")
    expect(admin).toMatchObject({ to: "/admin/cohorts", done: false })
  })
})

describe("試測帳號：不做入門前測，先綜合檢測再填問卷", () => {
  const fresh = { trial: true, pretest_done: false, survey_pending: true }

  it("剛掃完 QR code：帶去檢測，不帶去前測", () => {
    const line = mascotLine(summary(fresh))
    expect(line.action).toEqual({ label: "開始檢測", to: "/exam" })
    expect(line.highlight).toBe("bookshelf")
    expect(mascotPose(summary(fresh), false)).toBe("point")
    expect(pickBubbles(summary(fresh))[0]).toMatchObject({
      id: "bookshelf",
      highlight: true,
    })
  })

  it("檢測交卷後：帶去填問卷", () => {
    const line = mascotLine(summary({ ...fresh, survey_ready: true }))
    expect(line.action).toEqual({ label: "填問卷", to: "/survey" })
  })

  it("檢測進行中：照一般的檢測提示", () => {
    const line = mascotLine(summary({ ...fresh, exam_active_attempt_id: "a1" }))
    expect(line.action).toBeUndefined()
    expect(line.text).toBe("檢測做完前，練習先暫停。")
  })

  it("問卷交完：不再要求前測，選單可以再打開編號頁", () => {
    const done = summary({ trial: true, pretest_done: false })
    expect(mascotLine(done).action).toBeUndefined()
    expect(menuItems(done)[0]).toMatchObject({
      id: "survey",
      label: "試測完成",
      status: "看受試編號",
      to: "/survey",
    })
  })

  it("一般帳號沒做前測：照舊帶去前測", () => {
    const line = mascotLine(summary({ pretest_done: false }))
    expect(line.action?.to).toBe("/pretest")
  })
})
