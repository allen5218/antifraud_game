import { describe, expect, test } from "bun:test"
import {
  ART_H,
  ART_W,
  GROUND_Y,
  layoutCardArt,
  PHONE_SCREEN,
  parseCardArt,
  type Rect,
} from "./cardArtLayout"
import type { CastId } from "./cardArtManifest"

const people = (...ids: CastId[]) =>
  ids.map((id) => ({ id, pose: "neutral" as const }))

const inside = (r: Rect) =>
  r.x >= -r.w * 0.25 &&
  r.x + r.w <= ART_W + r.w * 0.25 &&
  r.y >= 0 &&
  r.y + r.h <= ART_H + 1
// 角色畫布左右各留了空白，真正的人大約佔中間六成寬
const body = (r: Rect) => ({ x: r.x + r.w * 0.2, w: r.w * 0.6 })

describe("讀 art 欄位", () => {
  test("pose 只套在第一個角色，其他人用 neutral", () => {
    const spec = parseCardArt({
      scene: "living-room",
      cast: ["grandma", "fake-cs"],
      pose: "worried",
    })
    expect(spec.scene).toBe("living-room")
    expect(spec.cast).toEqual([
      { id: "grandma", pose: "worried" },
      { id: "fake-cs", pose: "neutral" },
    ])
  })

  test("可以用 id:pose 個別指定表情", () => {
    const spec = parseCardArt({
      cast: ["grandma:happy", "fake-cs:talking-phone"],
      pose: "worried",
    })
    expect(spec.cast).toEqual([
      { id: "grandma", pose: "happy" },
      { id: "fake-cs", pose: "talking-phone" },
    ])
  })

  test("清單外的 id 與姿勢略過或退回 neutral，不會壞掉", () => {
    const spec = parseCardArt({
      scene: "moon",
      cast: ["alien", "grandpa:dancing", "police"],
      props: ["phone", "rocket", "phone"],
      pose: "flying",
    })
    expect(spec.scene).toBeNull()
    expect(spec.cast).toEqual([
      { id: "grandpa", pose: "neutral" },
      { id: "police", pose: "neutral" },
    ])
    expect(spec.props).toEqual(["phone"])
  })

  test("角色、道具最多各三個", () => {
    const spec = parseCardArt({
      cast: ["grandma", "grandpa", "student", "police"],
      props: ["phone", "chat", "card", "qr"],
    })
    expect(spec.cast.map((c) => c.id)).toEqual([
      "grandma",
      "grandpa",
      "student",
    ])
    expect(spec.props).toEqual(["phone", "chat", "card"])
  })

  test("什麼都沒有也可以", () => {
    expect(parseCardArt({})).toEqual({ scene: null, cast: [], props: [] })
  })
})

describe("排位", () => {
  test("一個人站在正中間，腳踩地面", () => {
    const { cast } = layoutCardArt({
      scene: "street",
      cast: people("grandma"),
      props: [],
    })
    expect(cast).toHaveLength(1)
    expect(cast[0].x + cast[0].w / 2).toBeCloseTo(ART_W / 2, 0)
    expect(cast[0].y + (cast[0].h * 226) / 240).toBeCloseTo(GROUND_Y, 0)
    expect(cast[0].mirror).toBe(false)
  })

  for (const count of [2, 3]) {
    test(`${count} 個人都在畫面裡、身體不重疊，最右邊的人轉向`, () => {
      const ids: CastId[] = ["grandma", "fake-cs", "police"]
      for (const props of [[], ["phone" as const]]) {
        const { cast } = layoutCardArt({
          scene: "living-room",
          cast: people(...ids.slice(0, count)),
          props,
        })
        expect(cast).toHaveLength(count)
        for (const slot of cast) expect(inside(slot)).toBe(true)
        for (let i = 1; i < cast.length; i++) {
          const a = body(cast[i - 1])
          const b = body(cast[i])
          expect(a.x + a.w).toBeLessThanOrEqual(b.x + 1)
        }
        expect(cast.at(-1)?.mirror).toBe(true)
        expect(cast[0].mirror).toBe(false)
      }
    })
  }

  test("有道具時角色讓到左邊，道具在右邊", () => {
    const { cast, props } = layoutCardArt({
      scene: "office",
      cast: people("office-worker", "fake-cs"),
      props: ["laptop", "atm"],
    })
    for (const slot of cast)
      expect(slot.x + slot.w / 2).toBeLessThan(ART_W * 0.7)
    for (const p of props) {
      expect(p.x + p.size / 2).toBeGreaterThan(ART_W * 0.65)
      expect(p.x + p.size).toBeLessThanOrEqual(ART_W)
      expect(p.y).toBeGreaterThanOrEqual(0)
    }
  })

  test("大道具放地上、小道具浮著墊白底", () => {
    const { props } = layoutCardArt({
      scene: "atm-corner",
      cast: people("grandma"),
      props: ["phone", "atm"],
    })
    const atm = props.find((p) => p.id === "atm")!
    const phone = props.find((p) => p.id === "phone")!
    expect(atm.bubble).toBe(false)
    expect(atm.y + (atm.size * 114) / 120).toBeCloseTo(GROUND_Y, 0)
    expect(phone.bubble).toBe(true)
    expect(phone.y + phone.size).toBeLessThan(atm.y + 1)
  })

  test("沒有角色時道具排在中間", () => {
    const { cast, props } = layoutCardArt({
      scene: null,
      cast: [],
      props: ["card", "money"],
    })
    expect(cast).toEqual([])
    expect(props).toHaveLength(2)
    const mid = (props[0].x + props[1].x + props[1].size) / 2
    expect(mid).toBeCloseTo(ART_W / 2, 0)
  })

  test("手機螢幕場景：主角在螢幕裡，第二人是右上角小視窗", () => {
    const { cast } = layoutCardArt({
      scene: "phone-screen",
      cast: people("police", "grandma"),
      props: ["card"],
    })
    expect(cast[0].clip).toEqual(PHONE_SCREEN)
    const pip = cast[1].clip!
    expect(pip.x).toBeGreaterThan(PHONE_SCREEN.x + PHONE_SCREEN.w / 2)
    expect(pip.y).toBeLessThan(PHONE_SCREEN.y + PHONE_SCREEN.h / 3)
    expect(pip.x + pip.w).toBeLessThanOrEqual(PHONE_SCREEN.x + PHONE_SCREEN.w)
  })

  test("一般場景的角色不裁切", () => {
    const { cast } = layoutCardArt({
      scene: "shop",
      cast: people("seller", "buyer"),
      props: [],
    })
    expect(cast.every((c) => c.clip === null)).toBe(true)
  })
})
