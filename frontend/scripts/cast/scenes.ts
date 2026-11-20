// 六個場景，畫布 400×300。角色站在 y≈284 的地面上，所以場景的地板從 y=212 左右開始。
// 細節壓低對比，角色和道具疊上去才看得清楚。

import type { SceneId } from "../../src/components/cards/cardArtManifest"
import { atmBody } from "./props"
import { seeded, shapes, withShade } from "./svg"

const WHITE = "#FFFDF8"
const GLASS = "#CFE3EC"
const PLANT = "#86B07F"
const PLANT_D = "#6F9A69"
const POT = "#C9714F"
const POT_D = "#A6583B"
const TEAL = "#6F9A92"
const GOLD = "#E2B45A"

const plant = (x: number, y: number, s = 1) =>
  `<g transform="translate(${x} ${y}) scale(${s})">${withShade(
    [
      { circle: [-10, -34, 13] },
      { circle: [10, -38, 14] },
      { circle: [0, -52, 12] },
    ],
    PLANT,
    PLANT_D,
    2,
    3,
  )}${shapes([{ d: "M-14-20h28l-4 22h-20Z" }], POT)}${shapes([{ d: "M-14-20h28v5h-28Z" }], POT_D)}</g>`

function floorPlanks(y: number, color: string, line: string): string {
  let s = shapes([{ rect: [0, y, 400, 300 - y] }], color)
  const rows = [y + 22, y + 48, y + 76]
  let d = ""
  rows.forEach((ry, i) => {
    const top = rows[i - 1] ?? y
    d += `M0 ${ry}H400`
    for (let x = 40 + i * 37; x < 400; x += 110) d += `M${x} ${top}V${ry}`
  })
  s += `<path d="${d}" fill="none" stroke="${line}" stroke-width="2"/>`
  return s
}

function livingRoom(): string {
  let s = shapes([{ rect: [0, 0, 400, 300] }], "#F3EBDD")
  s += floorPlanks(212, "#E2C9A6", "#D6BB95")
  s += shapes([{ rect: [0, 205, 400, 9] }], "#D9C3A2")
  // 窗與窗簾
  s += shapes([{ rect: [236, 38, 120, 100, 6] }], WHITE)
  s += shapes(
    [{ rect: [244, 46, 48, 84, 3] }, { rect: [300, 46, 48, 84, 3] }],
    GLASS,
  )
  s += shapes(
    [
      { d: "M252 112q20-14 40-4v22h-40Z" },
      { d: "M300 116q24-16 48-6v20h-48Z" },
    ],
    "#BFDCC8",
  )
  s += shapes([{ rect: [226, 30, 140, 5, 2.5] }], "#C79A6B")
  s += withShade(
    [{ d: "M224 33h22q-4 50 6 112h-30Z" }, { d: "M368 33h-22q4 50-6 112h30Z" }],
    "#E9B872",
    "#D49F57",
    2,
    0,
  )
  // 牆上的紅色斗方
  s += `<g transform="rotate(45 74 76)">${shapes([{ rect: [56, 58, 36, 36, 3] }], "#D9534A")}<rect x="61" y="63" width="26" height="26" rx="2" fill="none" stroke="${GOLD}" stroke-width="2"/></g>`
  // 沙發
  s += withShade([{ rect: [22, 146, 128, 46, 16] }], "#8FB1C9", "#7A9CB5", 0, 3)
  s += shapes([{ rect: [16, 178, 140, 34, 10] }], "#7A9CB5")
  s += shapes([{ rect: [24, 172, 124, 18, 8] }], "#9DBDD3")
  s += shapes(
    [{ rect: [8, 162, 24, 50, 10] }, { rect: [140, 162, 24, 50, 10] }],
    "#8FB1C9",
  )
  s += shapes(
    [{ rect: [22, 210, 6, 8, 2] }, { rect: [144, 210, 6, 8, 2] }],
    "#6E5444",
  )
  s += shapes([{ rect: [40, 152, 26, 22, 8] }], "#E9B872")
  // 盆栽
  s += plant(374, 214)
  return s
}

function street(): string {
  let s = shapes([{ rect: [0, 0, 400, 300] }], "#D6EAF0")
  // 三棟透天厝，一樓是騎樓
  const building = (
    x: number,
    y: number,
    w: number,
    wall: string,
    win: string,
  ) => {
    let b = shapes([{ rect: [x, y, w, 222 - y] }], wall)
    for (let wy = y + 16; wy < 150; wy += 34)
      for (let wx = x + 14; wx + 22 < x + w; wx += 36)
        b += shapes([{ rect: [wx, wy, 22, 20, 2] }], win)
    b += shapes([{ rect: [x, 160, w, 62] }], "#B9A58C")
    for (let px = x; px <= x + w - 12; px += 54)
      b += shapes([{ rect: [px, 160, 12, 62] }], wall)
    return b
  }
  s += building(0, 46, 128, "#E8D5B5", "#FFF6E6")
  s += building(128, 22, 132, "#DCC6AA", "#CFE3EC")
  s += building(260, 58, 140, "#EAD9C0", "#FFF6E6")
  // 直立招牌（不寫字，只放色塊）
  const sign = (x: number, y: number, h: number, fill: string) =>
    `${shapes([{ rect: [x, y, 20, h, 3] }], fill)}${shapes(
      Array.from({ length: Math.floor((h - 10) / 16) }, (_, i) => ({
        rect: [x + 5, y + 8 + i * 16, 10, 9, 2] as [
          number,
          number,
          number,
          number,
          number,
        ],
      })),
      WHITE,
      ' opacity=".85"',
    )}`
  s += sign(104, 64, 82, "#D9644A")
  s += sign(236, 36, 98, TEAL)
  s += sign(366, 76, 76, GOLD)
  s += shapes([{ rect: [140, 138, 104, 18, 3] }], WHITE)
  s += shapes([{ rect: [148, 144, 40, 6, 3] }], "#D9644A")
  // 電線
  s += `<path d="M0 30Q200 64 400 24M0 40Q190 78 400 36" fill="none" stroke="#7D6E62" stroke-width="1.5" opacity=".45"/>`
  // 人行道與馬路
  s += shapes([{ rect: [0, 222, 400, 26] }], "#D8D0C2")
  s += `<path d="M40 222v26M120 222v26M200 222v26M280 222v26M360 222v26" stroke="#C9C0B0" stroke-width="2"/>`
  s += shapes([{ rect: [0, 246, 400, 5] }], "#C2B8A8")
  s += shapes([{ rect: [0, 251, 400, 49] }], "#B5AFA8")
  s += `<path d="M10 278h40M90 278h40M170 278h40M250 278h40M330 278h40" stroke="#F1EDE6" stroke-width="4" stroke-linecap="round"/>`
  // 停在騎樓前的機車
  const scooter = (x: number, body: string, flip: boolean) =>
    `<g transform="translate(${x} 0)${flip ? " scale(-1 1)" : ""}">${shapes(
      [{ circle: [-22, 240, 8] }, { circle: [22, 240, 8] }],
      "#3A3A40",
    )}${shapes([{ d: "M-30 232q4-14 22-14h14l6 14Z" }, { d: "M12 232l4-26h8l2 26Z" }], body)}${shapes([{ rect: [-24, 210, 26, 8, 4] }], "#4A3A32")}${shapes([{ rect: [12, 200, 16, 4, 2] }], "#3A3A40")}${shapes([{ circle: [26, 212, 3] }], "#F6E7B0")}</g>`
  s += scooter(44, "#7C9CB8", false)
  s += scooter(352, "#E38E8A", true)
  return s
}

function atmCorner(): string {
  let s = shapes([{ rect: [0, 0, 400, 300] }], "#EEF0EC")
  let grid = ""
  for (let y = 25; y < 214; y += 25) grid += `M0 ${y}H400`
  for (let x = 25; x < 400; x += 25) grid += `M${x} 0V214`
  s += `<path d="${grid}" stroke="#E2E6E1" stroke-width="1.5"/>`
  s += shapes([{ rect: [0, 214, 400, 86] }], "#DAD5CC")
  s += `<path d="M0 240H400M0 270H400M60 214V300M160 214V300M260 214V300M360 214V300" stroke="#CDC7BC" stroke-width="2"/>`
  s += shapes([{ rect: [0, 208, 400, 7] }], "#C9C3B8")
  // 上方招牌
  s += shapes([{ rect: [70, 16, 260, 30, 6] }], TEAL)
  s += shapes([{ rect: [150, 25, 100, 12, 4] }], "#FFFFFF", ' opacity=".9"')
  // 兩台 ATM
  s += `<g transform="translate(66 62) scale(1.28)">${atmBody()}</g>`
  s += `<g transform="translate(180 62) scale(1.28)">${atmBody()}</g>`
  // 防詐海報
  s += withShade([{ rect: [334, 74, 52, 70, 3] }], WHITE, "#DCD6CB", 2, 3)
  s += shapes([{ rect: [334, 74, 52, 12, 3] }], "#D9644A")
  s += shapes([{ d: "M360 94l14 24h-28Z" }], GOLD)
  s += shapes(
    [{ rect: [358.5, 101, 3, 9, 1.5] }, { circle: [360, 114, 1.8] }],
    "#3A2C26",
  )
  s += shapes(
    [{ rect: [342, 124, 36, 4, 2] }, { rect: [342, 132, 26, 4, 2] }],
    "#C9C2B6",
  )
  // 地墊
  s += shapes([{ rect: [76, 230, 250, 22, 6] }], "#C3BDB2")
  return s
}

function shop(): string {
  let s = shapes([{ rect: [0, 0, 400, 300] }], "#F4EEE2")
  s += shapes([{ rect: [0, 0, 400, 14] }], TEAL)
  s += shapes([{ rect: [0, 14, 400, 7] }], GOLD)
  s += shapes([{ rect: [0, 214, 400, 86] }], "#E8E2D6")
  s += `<path d="M0 244H400M0 274H400M50 214V300M130 214V300M210 214V300M290 214V300M370 214V300" stroke="#DCD5C7" stroke-width="2"/>`
  // 左邊的貨架
  s += shapes([{ rect: [10, 52, 140, 162, 4] }], "#D9C3A2")
  s += shapes([{ rect: [18, 60, 124, 146] }], "#EADBC3")
  const rnd = seeded(7)
  const colors = [
    "#D2694F",
    "#E2B45A",
    "#6F9A92",
    "#8FB1C9",
    "#E38E8A",
    "#86B07F",
    "#F2E2C8",
  ]
  for (const shelfY of [98, 138, 178]) {
    s += shapes([{ rect: [14, shelfY, 132, 6, 2] }], "#C79A6B")
    let x = 22
    while (x < 136) {
      const w = 10 + Math.floor(rnd() * 8)
      const h = 18 + Math.floor(rnd() * 14)
      if (x + w > 140) break
      s += shapes(
        [{ rect: [x, shelfY - h, w, h, 2] }],
        colors[Math.floor(rnd() * colors.length)],
      )
      x += w + 3
    }
  }
  // 右邊的飲料冰箱
  s += shapes([{ rect: [262, 44, 128, 170, 6] }], "#DDE3E6")
  s += shapes(
    [{ rect: [270, 54, 54, 152, 3] }, { rect: [328, 54, 54, 152, 3] }],
    GLASS,
  )
  for (const [x0, y0] of [
    [274, 60],
    [332, 60],
  ])
    for (let row = 0; row < 4; row++)
      for (let col = 0; col < 4; col++)
        s += shapes(
          [{ rect: [x0 + col * 12, y0 + row * 37 + 8, 9, 26, 3] }],
          colors[(row * 3 + col + x0) % colors.length],
          ' opacity=".85"',
        )
  s += shapes(
    [{ rect: [318, 110, 3, 30, 1.5] }, { rect: [331, 110, 3, 30, 1.5] }],
    "#AEB3BA",
  )
  // 中間的促銷海報
  s += withShade([{ rect: [172, 64, 70, 64, 4] }], WHITE, "#DCD6CB", 2, 3)
  s += shapes([{ circle: [207, 92, 18] }], "#E38E8A")
  s += shapes([{ rect: [182, 114, 50, 6, 3] }], GOLD)
  return s
}

function office(): string {
  let s = shapes([{ rect: [0, 0, 400, 300] }], "#ECE7DF")
  s += shapes([{ rect: [0, 214, 400, 86] }], "#CFC8BC")
  s += shapes([{ rect: [0, 208, 400, 7] }], "#BDB5A8")
  // 有百葉窗的窗
  s += shapes([{ rect: [248, 36, 124, 112, 5] }], WHITE)
  s += shapes([{ rect: [256, 44, 108, 96, 2] }], GLASS)
  s += shapes([{ rect: [256, 44, 108, 52, 2] }], "#E6DED0")
  let blinds = ""
  for (let y = 52; y < 96; y += 8) blinds += `M256 ${y}H364`
  s += `<path d="${blinds}" stroke="#D3C9B8" stroke-width="2"/>`
  // 掛鐘
  s += shapes([{ circle: [184, 62, 17] }], WHITE)
  s += `<circle cx="184" cy="62" r="17" fill="none" stroke="#C9C2B6" stroke-width="3"/><path d="M184 62V51M184 62l7 4" stroke="#3A2C26" stroke-width="2.4" stroke-linecap="round"/>`
  // 辦公桌與電腦
  s += shapes([{ rect: [12, 168, 160, 10, 3] }], "#C79A6B")
  s += shapes([{ rect: [18, 178, 44, 36] }], "#B5895C")
  s += shapes(
    [{ rect: [24, 186, 32, 4, 2] }, { rect: [24, 200, 32, 4, 2] }],
    "#9C744B",
  )
  s += shapes([{ rect: [158, 178, 8, 36] }], "#B5895C")
  s += withShade([{ rect: [70, 110, 70, 46, 4] }], "#454A57", "#33363F", 2, 3)
  s += shapes([{ rect: [75, 115, 60, 36, 2] }], GLASS)
  s += shapes(
    [{ rect: [80, 121, 30, 4, 2] }, { rect: [80, 129, 44, 4, 2] }],
    "#FFFFFF",
    ' opacity=".85"',
  )
  s += shapes(
    [{ rect: [100, 156, 10, 10] }, { rect: [90, 164, 30, 4, 2] }],
    "#5A5F6C",
  )
  s += shapes([{ rect: [128, 156, 12, 12, 3] }], "#E38E8A")
  // 盆栽
  s += plant(368, 216, 1.1)
  return s
}

/** 手機螢幕場景：CardArt 會把角色畫進螢幕裡（像視訊），螢幕範圍見 PHONE_SCREEN */
export const PHONE_SCREEN = { x: 128, y: 74, w: 144, h: 210 }

function phoneScreen(): string {
  let s = shapes([{ rect: [0, 0, 400, 300] }], "#EFE6D8")
  s += shapes(
    [
      { circle: [56, 70, 34] },
      { circle: [350, 220, 46] },
      { circle: [330, 60, 14] },
      { circle: [70, 240, 20] },
    ],
    "#E6D8C4",
  )
  s += withShade([{ rect: [120, 8, 160, 288, 28] }], "#454A57", "#33363F", 4, 4)
  s += shapes([{ rect: [128, 22, 144, 262, 18] }], "#F7F4EE")
  s += shapes([{ rect: [176, 28, 48, 8, 4] }], "#454A57")
  // 對話標題列
  s += shapes([{ d: "M128 40h144v34H128Z" }], TEAL)
  s += shapes([{ circle: [148, 57, 10] }], "#FFFFFF", ' opacity=".8"')
  s += shapes([{ rect: [164, 50, 54, 6, 3] }], "#FFFFFF")
  s += shapes([{ rect: [164, 60, 34, 4, 2] }], "#FFFFFF", ' opacity=".7"')
  // 對話泡泡
  s += shapes(
    [{ rect: [138, 88, 82, 22, 11] }, { rect: [138, 160, 98, 34, 12] }],
    "#FFFFFF",
  )
  s += shapes(
    [{ rect: [186, 124, 76, 22, 11] }, { rect: [204, 208, 58, 22, 11] }],
    "#CDE6C7",
  )
  s += shapes([{ rect: [136, 256, 128, 20, 10] }], "#FFFFFF")
  s += shapes([{ circle: [254, 266, 7] }], TEAL)
  return s
}

export const SCENES: Record<SceneId, () => string> = {
  "living-room": livingRoom,
  street,
  "atm-corner": atmCorner,
  shop,
  office,
  "phone-screen": phoneScreen,
}
