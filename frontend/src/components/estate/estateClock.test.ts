import { expect, test } from "bun:test"
import type { EstatePublic, IndustryPublic } from "@/client"
import { projectCash, projectIndustry } from "./estateClock"

function industry(over: Partial<IndustryPublic> = {}): IndustryPublic {
  return {
    tier_id: 1,
    name: "雅房",
    image_url: "/assets/property/tier-1.webp",
    category: "general",
    category_label: "防詐基本功",
    owned: 2,
    next_price: 1254,
    revenue_per_cycle: 2,
    cycle_seconds: 6,
    income_per_hour: 1200,
    progress_seconds: 3,
    ready: false,
    manager: { item_id: "m1", name: "柴犬", image_url: "/x.webp" },
    card_level: 0,
    max_card_level: 8,
    card_price: 50000,
    doublings: 0,
    quantity_doublings: 0,
    card_doublings: 0,
    practice_doublings: 0,
    next_quantity_milestone: 25,
    practice_correct: 0,
    next_practice_milestone: 25,
    starter: true,
    ...over,
  }
}

test("有經理：進度條一直跑，跑滿幾次就收幾次租", () => {
  const now = projectIndustry(industry(), 10)
  // 3 + 10 = 13 秒：收了 2 次、這一輪走到 1/6
  expect(now.earned).toBe(4n)
  expect(now.ready).toBe(false)
  expect(now.progress).toBeCloseTo(1 / 6)
})

test("沒經理：跑滿就停在收租，不會自己加錢", () => {
  const now = projectIndustry(industry({ manager: null }), 10)
  expect(now).toEqual({ progress: 1, ready: true, earned: 0n })
})

test("沒有這種房產就不動", () => {
  expect(projectIndustry(industry({ owned: 0 }), 100).earned).toBe(0n)
})

test("畫面上的現金加上經理估計又收的", () => {
  const estate = {
    cash: 1000,
    industries: [industry(), industry({ tier_id: 2, manager: null })],
  } as unknown as EstatePublic
  expect(projectCash(estate, 10)).toBe(1004n)
})
